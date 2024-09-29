import tkinter
import customtkinter
import os
import shutil
from src.FaceCaptureAndAugmentation import FaceCaptureAndAugmentation  # Import the class
from src.FaceRecognitionAttendance import FaceRecognitionAttendance  # Import the class
from pymongo import MongoClient
import certifi
import datetime
import pytz

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light")
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # MongoDB Configuration
        client = MongoClient(
            'mongodb+srv://6420015:afterfallSP1@clusteraf.lcvf3mb.mongodb.net/?retryWrites=true&w=majority&appName=ClusterAF',
            tlsCAFile=certifi.where()
        )
        self.db = client['afterfall']  # Store the database reference as an instance variable
        self.collection_attendance = self.db['attendances']  # Collection for attendance
        self.collection_classes = self.db['classes']  # Collection for classes

        # Initialize FaceRecognitionAttendance instance with MongoDB attendance collection
        self.face_recognition_attendance = FaceRecognitionAttendance(
            dataset_path='data/dataset_faces',
            mongo_collection=self.collection_attendance  # MongoDB collection for attendance
        )

        # Class-level variable to store the matched classCode
        self.matched_class_code = None

        # Configure window
        self.title("AfterFall Face Recognition Admin")
        self.geometry(f"{780}x450")  # Set the window size here (width x height)

        # Configure grid layout (2x1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)  # Additional row for other functionalities

        # Create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="AfterFall", font=customtkinter.CTkFont(size=40, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Display Classes Button (Face Recognition)
        self.display_classes_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Face Recognition",
            command=self.show_display_classes_button,
            fg_color="blue",  # Button color
            hover_color="darkblue"  # Hover color
        )
        self.display_classes_button.grid(row=1, column=0, padx=20, pady=10)

        # Display Attendance Button
        self.display_attendance_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Attendance",
            command=self.display_attendance,
            fg_color="blue",  # Button color
            hover_color="darkblue"  # Hover color
        )
        self.display_attendance_button.grid(row=2, column=0, padx=20, pady=10)

        # Appearance mode label
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=3, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=4, column=0, padx=20, pady=(10, 10))

        # Create textbox for displaying data
        self.textbox = customtkinter.CTkTextbox(self, width=250)
        self.textbox.grid(row=0, column=1, padx=(20, 20), pady=(20, 10), sticky="nsew")

        # Create entry for user ID
        self.user_entry = customtkinter.CTkEntry(self, placeholder_text="Enter user ID")
        self.user_entry.grid(row=1, column=1, padx=(20, 20), pady=(10, 5), sticky="ew")

        # Create button for adding user
        self.add_user_button = customtkinter.CTkButton(
            self,
            text="Add user",
            command=self.add_user_folder,
            fg_color="green",  # Button color
            hover_color="darkgreen"  # Hover color
        )
        self.add_user_button.grid(row=2, column=1, padx=(20, 20), pady=(5, 5), sticky="ew")

        # Create button for deleting user
        self.delete_user_button = customtkinter.CTkButton(
            self,
            text="Delete User",
            command=self.delete_user_folder,
            fg_color="red",  # Button color
            hover_color="darkred"  # Hover color
        )
        self.delete_user_button.grid(row=3, column=1, padx=(20, 20), pady=(5, 20), sticky="ew")

        # Class-related widgets
        self.class_id_entry = customtkinter.CTkEntry(self, placeholder_text="Enter Class ID to Check")
        self.class_id_entry.grid_forget()  # Initially hide

        self.check_class_button = customtkinter.CTkButton(
            self,
            text="Check Class ID",
            command=self.check_class_id_match,
            fg_color="blue",  # Button color
            hover_color="darkblue"  # Hover color
        )
        self.check_class_button.grid_forget()  # Initially hide

        # Initially hide all delete widgets
        self.hide_all_delete_widgets()

        # Set default values
        self.appearance_mode_optionemenu.set("Dark")
        self.textbox.insert("0.0", "Hello, welcome to our Assumption University Senior Project 1\n\n"
                                   "Contributors (AfterFall team):\n"
                                   "- LORENZO MARTINS DALMEIDA\n"
                                   "- ARCHIT CHANGCHREONKUL\n"
                                   "- KRITSADA KRUAPAT\n\n"
                                   "Advisor of this project:\n"
                                   "- DOBRI ATANASSOV BATOVSKI\n")

    def initialize_face_recognition(self):
        tkinter.messagebox.showinfo("Webcam Instruction", "Press 'q' to end the webcam.")

        matched_class_code = self.matched_class_code  # Retrieve the matched class code stored earlier

        if matched_class_code:
            # Start face recognition and log attendance using detected user_id from the face recognition process
            self.face_recognition_attendance.process_video_stream(matched_class_code)  # Pass matched_class_code
        else:
            tkinter.messagebox.showerror("Error", "No matched class code found.")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)
        self.hide_all_delete_widgets()

    def display_attendance(self):
        try:
            # Fetch all attendance records from the MongoDB collection
            attendance_records = list(self.face_recognition_attendance.mongo_collection.find({}))

            if not attendance_records:
                self.textbox.delete("1.0", tkinter.END)
                self.textbox.insert("1.0", "No attendance records found.")
                return

            # Prepare a string to hold all the attendance data
            attendance_data = ""

            # Define the Thai timezone
            thai_timezone = pytz.timezone('Asia/Bangkok')

            # Iterate over all attendance records
            for record in attendance_records:
                user_id = record.get('UserID', 'Unknown')
                class_id = record.get('classID', 'Unknown')
                attendance_list = record.get('attendance', [])

                # Add the user and class information
                attendance_data += f"UserID: {user_id} ClassID: {class_id}\n"

                # Append each attendance timestamp, converting it to Thai time for display purposes only
                for timestamp in attendance_list:
                    utc_time = timestamp  # Assuming the timestamp is stored in UTC in the database
                    utc_time = utc_time.replace(tzinfo=pytz.utc)  # Attach UTC timezone if needed

                    # Convert UTC time to Thai timezone for display
                    thai_time = utc_time.astimezone(thai_timezone)

                    # Format the time for display
                    formatted_time = thai_time.strftime('%Y-%m-%d %H:%M:%S')  # Format the time
                    attendance_data += f"  - {formatted_time} (Thai Time)\n"

                attendance_data += "\n"  # Separate records with a newline for clarity

            # Display the attendance data in the textbox
            self.textbox.delete("1.0", tkinter.END)
            self.textbox.insert("1.0", attendance_data)

            self.hide_all_delete_widgets()

        except Exception as e:
            self.textbox.delete("1.0", tkinter.END)
            self.textbox.insert("1.0", f"Error retrieving attendance data: {e}")

    def show_display_classes_button(self):
        """
        Fetch and display all class codes from the 'classes' collection in the MongoDB database.
        Show the check class ID button and an entry to verify class ID matches.
        """
        self.hide_all_delete_widgets()  # Hide all other widgets before displaying class widgets

        try:
            # Use the initialized classes collection from __init__
            mongo_data = list(self.collection_classes.find({}, {'classCode': 1, '_id': 0}))  # Fetch only classCode field

            if not mongo_data:
                tkinter.messagebox.showinfo("Info", "No classes found in MongoDB.")
                return

            # Prepare data to display all class codes
            class_data = "Class Codes in the Database:\n\n"
            class_codes = set()

            for record in mongo_data:
                class_code = record.get("classCode", "Unknown")
                class_codes.add(class_code)

            for class_code in class_codes:
                class_data += f"Class Code: {class_code}\n"

            # Display the class codes in the textbox
            self.textbox.delete("1.0", tkinter.END)
            self.textbox.insert("1.0", class_data)

            # Show the class-related widgets
            self.class_id_entry.grid(row=3, column=1, padx=(20, 20), pady=(5, 5), sticky="ew")
            self.check_class_button.grid(row=4, column=1, padx=(20, 20), pady=(5, 20), sticky="ew")

        except Exception as e:
            tkinter.messagebox.showerror("Error", f"An error occurred while fetching class codes: {e}")

    def check_class_id_match(self):
        """
        Check if the input class code matches any class codes in the MongoDB 'classes' collection.
        If a match is found, store it in the class-level variable self.matched_class_code and start the face recognition webcam.
        """
        input_class_code = self.class_id_entry.get().strip()  # Assuming the entry field is still named class_id_entry

        if not input_class_code:
            tkinter.messagebox.showinfo("Info", "Please enter a class code.")
            return

        try:
            # Fetch all class codes from the MongoDB 'classes' collection
            mongo_data = list(self.collection_classes.find({}, {'classCode': 1, '_id': 0}))  # Use collection_classes

            # Extract class codes from the database
            class_codes = {record.get("classCode", "Unknown") for record in mongo_data}

            if input_class_code in class_codes:
                # Class code matches, store the matched classCode
                self.matched_class_code = input_class_code
                tkinter.messagebox.showinfo("Match Found", f"The class code '{self.matched_class_code}' matches a class in the database.\nStarting webcam for face detection...")
                self.initialize_face_recognition()  # Start the webcam and face detection
            else:
                tkinter.messagebox.showinfo("No Match", f"The class code '{input_class_code}' does not match any class in the database.")

        except Exception as e:
            tkinter.messagebox.showerror("Error", f"An error occurred while checking class codes: {str(e)}")

    def start_face_recognition(self):
        if self.face_recognition_attendance:
            self.face_recognition_attendance.process_video_stream()
        else:
            tkinter.messagebox.showerror("Error", "Webcam is not initialized. Please click 'Start Webcam' first.")

    def hide_class_widgets(self):
        """Hides the class ID entry and check button."""
        self.class_id_entry.grid_forget()  # Hide the entry
        self.check_class_button.grid_forget()  # Hide the button

if __name__ == "__main__":
    app = App()
    app.mainloop()
