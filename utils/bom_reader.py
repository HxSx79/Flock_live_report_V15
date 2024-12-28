import pandas as pd
import os
from typing import Dict

class BOMReader:
    def __init__(self, bom_file: str = "BOM.xlsx", scrap_file: str = "Scrap_Book.xlsx"):
        self.bom_file = bom_file
        self.scrap_file = scrap_file
        self.bom_data = None
        self.scrap_data = None
        self._load_bom()
        self._load_scrap_book()

    def _load_bom(self) -> None:
        """Load BOM data from Excel file"""
        if not os.path.exists(self.bom_file):
            print(f"Warning: BOM file not found: {self.bom_file}")
            self.bom_data = pd.DataFrame(columns=['Class_Name', 'Program', 'Part_Number', 'Part_Description', 'Target'])
        else:
            try:
                self.bom_data = pd.read_excel(self.bom_file)
                print(f"Successfully loaded BOM with {len(self.bom_data)} entries")
            except Exception as e:
                print(f"Error loading BOM: {e}")
                self.bom_data = pd.DataFrame(columns=['Class_Name', 'Program', 'Part_Number', 'Part_Description', 'Target'])

    def _load_scrap_book(self) -> None:
        """Load scrap codes from Excel file"""
        if not os.path.exists(self.scrap_file):
            print(f"Warning: Scrap book file not found: {self.scrap_file}")
            self.scrap_data = pd.DataFrame(columns=['Defect_Code', 'Description'])
        else:
            try:
                self.scrap_data = pd.read_excel(self.scrap_file)
                print(f"Successfully loaded Scrap Book with {len(self.scrap_data)} entries")
            except Exception as e:
                print(f"Error loading Scrap Book: {e}")
                self.scrap_data = pd.DataFrame(columns=['Defect_Code', 'Description'])

    def get_part_info(self, class_name: str) -> Dict[str, str]:
        """Get part information for a given class name"""
        if self.bom_data is None:
            return self._get_unknown_part_info()

        try:
            # Find matching row in BOM
            matching_row = self.bom_data[self.bom_data['Class_Name'] == class_name]
            
            if not matching_row.empty:
                row = matching_row.iloc[0]
                print(f"\nDebug - BOM Reader - Found part info for {class_name}:")
                print(f"  Program: {row['Program']}")
                print(f"  Part Number: {row['Part_Number']}")
                print(f"  Description: {row['Part_Description']}")
                # Ensure target is a number
                try:
                    target = int(float(row['Target']))
                    print(f"  Target (raw): {row['Target']}, Type: {type(row['Target'])}")
                    print(f"  Target (converted): {target}, Type: {type(target)}")
                except (ValueError, TypeError):
                    print(f"Warning: Invalid target value in BOM: {row['Target']}")
                    target = 0
                
                return {
                    'program': str(row['Program']),
                    'part_number': str(row['Part_Number']),
                    'part_description': str(row['Part_Description']),
                    'target': str(target)
                }
            else:
                print(f"Class name not found in BOM: {class_name}")
                return self._get_unknown_part_info()
                
        except Exception as e:
            print(f"Error retrieving part info: {e}")
            return self._get_unknown_part_info()

    def _get_unknown_part_info(self) -> Dict[str, str]:
        """Return default values for unknown parts"""
        return {
            'program': 'Unknown',
            'part_number': 'Unknown',
            'part_description': 'Unknown',
            'target': '0'
        }

    def get_unique_programs(self):
        """Get list of unique programs from BOM"""
        try:
            if self.bom_data is None:
                return []
            # Get unique values from the 'Program' column
            programs = self.bom_data['Program'].dropna().unique().tolist()
            return [str(program) for program in programs]  # Convert all to strings
        except Exception as e:
            print(f"Error getting unique programs: {str(e)}")
            return []

    def get_parts_by_program(self, program):
        """Get all parts for a specific program"""
        try:
            if self.bom_data is None:
                return []
            # Filter rows by program and create list of dictionaries
            parts_df = self.bom_data[self.bom_data['Program'] == program]
            return [
                {
                    'part_number': str(row['Part_Number']),
                    'part_description': str(row['Part_Description']),
                    'program': str(row['Program'])
                }
                for _, row in parts_df.iterrows()
            ]
        except Exception as e:
            print(f"Error getting parts for program {program}: {str(e)}")
            return []

    def get_defect_codes(self):
        """Get list of defect codes from Scrap Book"""
        try:
            if self.scrap_data is None:
                return []
            # Get values from column A (Defect Code)
            codes = self.scrap_data.iloc[:, 0].dropna().unique().tolist()
            return [str(code) for code in codes]
        except Exception as e:
            print(f"Error getting defect codes: {str(e)}")
            return []

    def get_defect_descriptions(self):
        """Get list of descriptions from Scrap Book"""
        try:
            if self.scrap_data is None:
                return []
            # Get values from column B (Description)
            descriptions = self.scrap_data.iloc[:, 1].dropna().unique().tolist()
            return [str(desc) for desc in descriptions]
        except Exception as e:
            print(f"Error getting descriptions: {str(e)}")
            return []

    def get_description_for_code(self, code):
        """Get description for a given defect code"""
        try:
            if self.scrap_data is None:
                return None
            matching_row = self.scrap_data[self.scrap_data.iloc[:, 0] == code]
            if not matching_row.empty:
                return str(matching_row.iloc[0, 1])
            return None
        except Exception as e:
            print(f"Error getting description for code {code}: {str(e)}")
            return None

    def get_code_for_description(self, description):
        """Get defect code for a given description"""
        try:
            if self.scrap_data is None:
                return None
            matching_row = self.scrap_data[self.scrap_data.iloc[:, 1] == description]
            if not matching_row.empty:
                return str(matching_row.iloc[0, 0])
            return None
        except Exception as e:
            print(f"Error getting code for description {description}: {str(e)}")
            return None