import os
import sys
from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
from datetime import datetime
from threading import Thread
from queue import Queue
from utils.video import VideoStream
from utils.detection import ObjectDetector
from utils.production_tracker import ProductionTracker
from utils.config import Config
from utils.event_manager import EventManager
from utils.bom_reader import BOMReader
import pandas as pd
from pathlib import Path

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
config = Config()
video_stream = VideoStream()
detector = ObjectDetector()
production_tracker = ProductionTracker()
frame_queue = Queue(maxsize=10)  # Buffer for frames

# Store scrap history in memory
scrap_history = []

# Set up event manager with socket
event_manager = EventManager.get_instance()
event_manager.set_socket(socketio)

# Initialize BOM reader
bom_reader = BOMReader()

def video_feed_producer():
    """Produce video frames in a separate thread"""
    for frame in video_stream.generate_frames(detector):
        if frame_queue.full():
            try:
                frame_queue.get_nowait()  # Remove old frame if queue is full
            except:
                pass
        frame_queue.put(frame)

@app.route('/')
def index():
    current_time = datetime.now().strftime("%H:%M:%S")
    current_datetime = datetime.now().strftime("%A, %B %d, %Y %H:%M:%S")
    
    # Get initial data from production tracker
    initial_data = production_tracker.get_all_data()
    
    # Debug - Log the exact data being used for Current Part Line sections
    print("\nDebug - Data for index.html Current Part sections:")
    print("Current Part Line 1:")
    print(f"  Program: {initial_data['line1_part']['program']!r}")  # !r shows quotes and escapes
    print(f"  Part Number: {initial_data['line1_part']['part_number']!r}")
    print(f"  Part Description: {initial_data['line1_part']['part_description']!r}")
    print("Current Part Line 2:")
    print(f"  Program: {initial_data['line2_part']['program']!r}")
    print(f"  Part Number: {initial_data['line2_part']['part_number']!r}")
    print(f"  Part Description: {initial_data['line2_part']['part_description']!r}")
    print("\nDebug - HTML template variables:")
    print(f"line1_part: {initial_data['line1_part']}")
    print(f"line2_part: {initial_data['line2_part']}")
    
    return render_template('index.html',
                         current_time=current_time,
                         current_datetime=current_datetime,
                         **initial_data)

@app.route('/production_data')
def get_production_data():
    """API endpoint to get latest production data"""
    try:
        data = production_tracker.get_all_data()
        data['current_time'] = datetime.now().strftime("%H:%M:%S")
        
        # Debug - Log polling request
        print(f"\nDebug - Production data polled at {data['current_time']}")
        
        # Debug - Print raw data from production tracker
        print(f"Line 1 part raw: {data['line1_part']}")
        print(f"Line 2 part raw: {data['line2_part']}")
        
        # Ensure data is properly formatted for JSON response
        response = {
            'line1_part': {
                'program': str(data['line1_part'].get('program', '')).strip(),
                'part_number': str(data['line1_part'].get('part_number', '')).strip(),
                'part_description': str(data['line1_part'].get('part_description', '')).strip(),
                'track_id': str(data['line1_part'].get('track_id', '')).strip(),
                'target': str(data['line1_part'].get('target', '0')).strip(),
                'class_name': str(data['line1_part'].get('class_name', '')).strip()
            },
            'line2_part': {
                'program': str(data['line2_part'].get('program', '')).strip(),
                'part_number': str(data['line2_part'].get('part_number', '')).strip(),
                'part_description': str(data['line2_part'].get('part_description', '')).strip(),
                'track_id': str(data['line2_part'].get('track_id', '')).strip(),
                'target': str(data['line2_part'].get('target', '0')).strip(),
                'class_name': str(data['line2_part'].get('class_name', '')).strip()
            },
            'line1_production': data.get('line1_production', {'quantity': 0, 'delta': 0}),
            'line2_production': data.get('line2_production', {'quantity': 0, 'delta': 0}),
            'line1_scrap': data.get('line1_scrap', {'total': 0, 'rate': 0}),
            'line2_scrap': data.get('line2_scrap', {'total': 0, 'rate': 0}),
            'total_quantity': data.get('total_quantity', 0),
            'total_delta': data.get('total_delta', 0),
            'total_scrap': data.get('total_scrap', 0),
            'average_scrap_rate': data.get('average_scrap_rate', 0),
            'current_time': data['current_time']
        }
        
        # Debug - Print the exact JSON that will be sent
        print("\nDebug - JSON Response before serialization:")
        print(f"Line 1 part: {response['line1_part']}")
        print(f"Line 2 part: {response['line2_part']}")
        
        json_response = jsonify(response)
        
        # Debug - Print the actual JSON string that will be sent
        print("\nDebug - Final JSON string:")
        print(json_response.get_data(as_text=True))
        
        return json_response
    except Exception as e:
        print(f"Error in get_production_data: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            frame = frame_queue.get()
            yield frame

    headers = {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'X-Accel-Buffering': 'no'
    }
    return Response(generate(),
                   mimetype='multipart/x-mixed-replace; boundary=frame',
                   headers=headers,
                   direct_passthrough=True)

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'success': False, 'error': 'No video file provided'})
    
    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({'success': False, 'error': 'No video file selected'})
    
    try:
        video_stream.set_test_video(video_file)
        detector.line_counter.reset_counts()
        
        # Clear frame queue and restart video feed thread
        while not frame_queue.empty():
            frame_queue.get()
        
        if hasattr(app, 'video_thread') and app.video_thread.is_alive():
            # Wait for old thread to finish
            app.video_thread.join(timeout=1.0)
        
        # Start new video feed thread
        app.video_thread = Thread(target=video_feed_producer, daemon=True)
        app.video_thread.start()
        
        return jsonify({'success': True, 'message': 'Video uploaded successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def emit_update():
    """Emit update event through WebSocket"""
    data = production_tracker.get_all_data()
    data['current_time'] = datetime.now().strftime("%H:%M:%S")
    
    # Ensure data is properly formatted for JSON response
    formatted_data = {
        'line1_part': {
            'program': str(data['line1_part'].get('program', '')).strip(),
            'part_number': str(data['line1_part'].get('part_number', '')).strip(),
            'part_description': str(data['line1_part'].get('part_description', '')).strip(),
            'track_id': str(data['line1_part'].get('track_id', '')).strip(),
            'target': str(data['line1_part'].get('target', '0')).strip(),
            'class_name': str(data['line1_part'].get('class_name', '')).strip()
        },
        'line2_part': {
            'program': str(data['line2_part'].get('program', '')).strip(),
            'part_number': str(data['line2_part'].get('part_number', '')).strip(),
            'part_description': str(data['line2_part'].get('part_description', '')).strip(),
            'track_id': str(data['line2_part'].get('track_id', '')).strip(),
            'target': str(data['line2_part'].get('target', '0')).strip(),
            'class_name': str(data['line2_part'].get('class_name', '')).strip()
        },
        'line1_production': data['line1_production'],
        'line2_production': data['line2_production'],
        'line1_scrap': data['line1_scrap'],
        'line2_scrap': data['line2_scrap'],
        'total_quantity': data['total_quantity'],
        'total_delta': data['total_delta'],
        'total_scrap': data['total_scrap'],
        'average_scrap_rate': data['average_scrap_rate'],
        'current_time': data['current_time'],
        'total_tbp_line1': data.get('total_tbp_line1', 0),
        'total_tbp_line2': data.get('total_tbp_line2', 0)
    }
    
    socketio.emit('production_update', formatted_data)

# Scrap Report Routes
@app.route('/scrap')
def scrap_report():
    current_time = datetime.now().strftime('%I:%M:%S %p')
    current_datetime = datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')
    return render_template('scrap_report.html', current_time=current_time, current_datetime=current_datetime)

def get_current_calendar_week():
    return f"cw{datetime.now().isocalendar()[1]:02d}"

def save_scrap_to_excel(scrap_data):
    try:
        # Create the filename with current calendar week
        calendar_week = get_current_calendar_week()
        filename = f"flock_scrap_data_{calendar_week}.xlsx"
        
        # Create new scrap entry
        new_entry = {
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Line': scrap_data['line'],
            'Program': scrap_data.get('program', ''),
            'Part Number': scrap_data.get('part_number', ''),
            'Defect Code': scrap_data['defect_code'],
            'Description': scrap_data['defect_description'],
            'Comments': scrap_data.get('comments', '')
        }
        
        # Initialize DataFrame
        if os.path.exists(filename):
            try:
                df = pd.read_excel(filename)
                # Add new entry at the top
                df = pd.concat([pd.DataFrame([new_entry]), df], ignore_index=True)
            except Exception as e:
                print(f"Error reading existing Excel file: {str(e)}")
                df = pd.DataFrame([new_entry])
        else:
            df = pd.DataFrame([new_entry])
        
        try:
            # Create a Pandas Excel writer using XlsxWriter as the engine
            with pd.ExcelWriter(filename, engine='xlsxwriter', mode='w') as writer:
                # Write the DataFrame to the Excel file
                df.to_excel(writer, index=False, sheet_name='Sheet1')
                
                # Get the workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['Sheet1']
                
                # Create formats
                header_format = workbook.add_format({
                    'bold': True,
                    'align': 'center',
                    'valign': 'vcenter',
                    'bg_color': '#D3D3D3'
                })
                
                cell_format = workbook.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'text_wrap': True
                })
                
                # Format headers
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Format all data cells
                for row in range(1, len(df) + 1):
                    for col in range(len(df.columns)):
                        worksheet.write(row, col, df.iloc[row-1, col], cell_format)
                
                # Auto-fit columns
                for col_num, column in enumerate(df.columns):
                    # Get the maximum length in the column
                    max_length = max(
                        df[column].astype(str).apply(len).max(),
                        len(str(column))
                    ) + 2  # Add some padding
                    
                    # Set column width
                    worksheet.set_column(col_num, col_num, max_length)
            
            print(f"Scrap data saved to {filename} with formatting")
            return True
            
        except Exception as e:
            print(f"Error writing formatted Excel file: {str(e)}")
            # Fallback to basic save if formatting fails
            df.to_excel(filename, index=False)
            print(f"Scrap data saved without formatting to {filename}")
            return True
            
    except Exception as e:
        print(f"Error saving scrap data to Excel: {str(e)}")
        return False

@app.route('/submit_scrap', methods=['POST'])
def submit_scrap():
    global scrap_history
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Add timestamp to the scrap report
        scrap_entry = {
            'time': datetime.now().strftime('%m/%d/%Y %I:%M:%S %p'),
            'line': data['line'],
            'program': data.get('program', ''),
            'part_number': data.get('part_number', ''),
            'defect_code': data['defect_code'],
            'defect_description': data['defect_description'],
            'comments': data.get('comments', '')
        }
        
        # Save to Excel file
        save_scrap_to_excel(scrap_entry)
        
        # Add to history (in memory)
        scrap_history.insert(0, scrap_entry)
        
        # Keep only the last 100 entries in memory
        if len(scrap_history) > 100:
            scrap_history.pop()
            
        # Update production tracker with scrap data
        if production_tracker:
            try:
                line_key = f"Line {data['line']}"
                production_tracker.update_scrap(line_key, 1)  # Always increment by 1
                
                # Get scrap-related data with proper structure
                line1_scrap_data = production_tracker.line_data.get('Line 1', {}).get('scrap', {'total': 0, 'rate': 0})
                line2_scrap_data = production_tracker.line_data.get('Line 2', {}).get('scrap', {'total': 0, 'rate': 0})
                
                scrap_data = {
                    'line1_scrap': {
                        'total': line1_scrap_data.get('total', 0),
                        'rate': line1_scrap_data.get('rate', 0)
                    },
                    'line2_scrap': {
                        'total': line2_scrap_data.get('total', 0),
                        'rate': line2_scrap_data.get('rate', 0)
                    },
                    'total_scrap': getattr(production_tracker, 'total_scrap', 0),
                    'average_scrap_rate': getattr(production_tracker, 'average_scrap_rate', 0)
                }
                
                # Emit scrap update with proper structure
                socketio.emit('scrap_update', scrap_data)
            except Exception as e:
                print(f"Error updating production tracker: {str(e)}")
                # Continue execution even if production tracker update fails
            
        return jsonify(scrap_entry), 200
        
    except Exception as e:
        print(f"Error submitting scrap: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_scrap_history')
def get_scrap_history():
    global scrap_history
    return jsonify(scrap_history)

@app.route('/get_programs')
def get_programs():
    """Get list of unique programs from BOM"""
    try:
        programs = bom_reader.get_unique_programs()
        return jsonify(sorted(programs))
    except Exception as e:
        print(f"Error getting programs: {str(e)}")
        return jsonify([]), 500

@app.route('/get_parts/<program>')
def get_parts(program):
    """Get parts for a specific program from BOM"""
    try:
        parts = bom_reader.get_parts_by_program(program)
        return jsonify(parts)
    except Exception as e:
        print(f"Error getting parts: {str(e)}")
        return jsonify([]), 500

@app.route('/get_defect_codes')
def get_defect_codes():
    """Get list of defect codes from Scrap Book"""
    try:
        codes = bom_reader.get_defect_codes()
        return jsonify(sorted(codes))
    except Exception as e:
        print(f"Error getting defect codes: {str(e)}")
        return jsonify([]), 500

@app.route('/get_defect_descriptions')
def get_defect_descriptions():
    """Get list of descriptions from Scrap Book"""
    try:
        descriptions = bom_reader.get_defect_descriptions()
        return jsonify(sorted(descriptions))
    except Exception as e:
        print(f"Error getting descriptions: {str(e)}")
        return jsonify([]), 500

@app.route('/get_description/<code>')
def get_description(code):
    """Get description for a defect code"""
    try:
        description = bom_reader.get_description_for_code(code)
        return jsonify({'description': description}) if description else ('', 404)
    except Exception as e:
        print(f"Error getting description: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_code/<description>')
def get_code(description):
    """Get defect code for a description"""
    try:
        code = bom_reader.get_code_for_description(description)
        return jsonify({'code': code}) if code else ('', 404)
    except Exception as e:
        print(f"Error getting code: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Start initial video feed thread
    app.video_thread = Thread(target=video_feed_producer, daemon=True)
    app.video_thread.start()
    
    socketio.run(app, host='0.0.0.0', port=8080, debug=False)