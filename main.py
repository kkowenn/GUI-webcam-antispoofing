import tkinter
import customtkinter
import os
import shutil
from src.FaceCaptureAndAugmentation import FaceCaptureAndAugmentation  # Import the class
from src.FaceRecognitionAttendance import FaceRecognitionAttendance  # Import the class
from pymongo import MongoClient
import certifi
import datetime

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
        db = client['afterfall']
        collection = db['attendance']

        # Initialize FaceRecognitionAttendance instance with MongoDB collection
        self.face_recognition_attendance = FaceRecognitionAttendance(
            dataset_path='data/dataset_faces',
            mongo_collection=collection  # Removed the CSV path since it's not needed anymore
        )

        # Configure window
        self.title("AfterFall Face Recognition")
        self.geometry(f"{780}x450")  # Set the window size here (width x height)

        # Configure grid layout (2x1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)  # Additional row for delete functionality

        # Create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="AfterFall", font=customtkinter.CTkFont(size=40, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Start Webcam Button
        self.start_webcam_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Start Webcam",
            command=self.initialize_face_recognition,
            fg_color="blue",  # Button color
            hover_color="darkblue"  # Hover color
        )
        self.start_webcam_button.grid(row=1, column=0, padx=20, pady=10)

        # Display User Button
        self.display_folders_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Display User",
            command=self.display_user_folders,
            fg_color="blue",  # Button color
            hover_color="darkblue"  # Hover color
        )
        self.display_folders_button.grid(row=2, column=0, padx=20, pady=10)

        # Display Attendance Button
        self.display_attendance_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Display Attendance",
            command=self.display_attendance,
            fg_color="blue",  # Button color
            hover_color="darkblue"  # Hover color
        )
        self.display_attendance_button.grid(row=3, column=0, padx=20, pady=10)

        # Appearance mode label
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))

        # Create textbox for displaying data
        self.textbox = customtkinter.CTkTextbox(self, width=250)
        self.textbox.grid(row=0, column=1, padx=(20, 20), pady=(20, 10), sticky="nsew")

        # Create entry for user ID (Used for both adding and deleting users)
        self.user_entry = customtkinter.CTkEntry(self, placeholder_text="Enter user ID")
        self.user_entry.grid(row=1, column=1, padx=(20, 20), pady=(10, 5), sticky="ew")

        # Create button for adding user
        self.add_user_button = customtkinter.CTkButton(
            self,
            text="Add User",
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

        # Create button for deleting entire attendance records in MongoDB
        self.delete_attendance_button = customtkinter.CTkButton(
            self,
            text="Delete Attendance",
            command=self.delete_attendance_records,
            fg_color="red",  # Button color
            hover_color="darkred"  # Hover color
        )

        # Initially hide the delete widgets
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
        self.start_face_recognition()  # Automatically start face recognition after initializing

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)
        self.hide_all_delete_widgets()

    def display_attendance(self):
        self.show_delete_attendance_button()

        try:
            # Fetch data from MongoDB
            mongo_data = list(self.face_recognition_attendance.mongo_collection.find({}, {'_id': 0}))  # Exclude '_id' field from MongoDB documents

            if not mongo_data:
                tkinter.messagebox.showinfo("Info", "No attendance data found in MongoDB.")
                return

            attendance_data = ""
            for record in mongo_data:
                user_id = record.get("UserID", "Unknown")
                timestamps = record.get("attendance", [])

                if isinstance(timestamps, datetime.datetime):
                    timestamps = [timestamps]

                attendance_data += f"UserID: {user_id}\n"
                for timestamp in timestamps:
                    attendance_data += f"  - {timestamp}\n"
                attendance_data += "\n"

            self.textbox.delete("1.0", tkinter.END)
            self.textbox.insert("1.0", attendance_data)

        except Exception as e:
            tkinter.messagebox.showerror("Error", f"An error occurred while fetching data from MongoDB: {str(e)}")

    def display_user_folders(self):
        self.show_delete_user_widgets()
        folder_path = "data/dataset_faces"
        try:
            folders = os.listdir(folder_path)
            folders = [folder for folder in folders if folder != ".DS_Store"]
            folder_names = "\n".join(f"User ID {index + 1}: {folder}" for index, folder in enumerate(folders))
            self.textbox.delete("1.0", tkinter.END)
            self.textbox.insert("1.0", folder_names)
        except FileNotFoundError:
            tkinter.messagebox.showerror("Error", f"The folder path '{folder_path}' was not found.")
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def add_user_folder(self):
        user_id = self.user_entry.get()

        if not user_id:
            tkinter.messagebox.showerror("Error", "Please enter a user ID to add.")
            return

        try:
            face_capture = FaceCaptureAndAugmentation(user_id=user_id)
            face_capture.capture_faces()  # Capture faces
            face_capture.augment_faces()  # Perform augmentation

            tkinter.messagebox.showinfo("Success", f"User with ID '{user_id}' has been added with captured and augmented faces.")
            self.display_user_folders()  # Refresh the displayed list of users
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"An error occurred while adding the user: {str(e)}")

    def delete_user_folder(self):
        user_id = self.user_entry.get()

        if not user_id:
            tkinter.messagebox.showerror("Error", "Please enter a user ID to delete.")
            return

        target_folder = os.path.join("data/dataset_faces", user_id)

        if os.path.exists(target_folder):
            try:
                shutil.rmtree(target_folder)
                tkinter.messagebox.showinfo("Success", f"User with ID '{user_id}' has been deleted.")
                self.display_user_folders()  # Refresh the displayed list of users
            except Exception as e:
                tkinter.messagebox.showerror("Error", f"An error occurred while deleting the user: {str(e)}")
        else:
            tkinter.messagebox.showerror("Error", f"The user with ID '{user_id}' does not exist.")

    def delete_attendance_records(self):
        try:
            # Delete all documents in MongoDB attendance collection
            result = self.face_recognition_attendance.mongo_collection.delete_many({})
            if result.deleted_count > 0:
                tkinter.messagebox.showinfo("Success", "Attendance data deleted from MongoDB.")
            else:
                tkinter.messagebox.showinfo("Info", "No data to delete in MongoDB.")

        except Exception as e:
            tkinter.messagebox.showerror("Error", f"An error occurred while deleting attendance data: {str(e)}")

    def start_face_recognition(self):
        if self.face_recognition_attendance:
            self.face_recognition_attendance.process_video_stream()
        else:
            tkinter.messagebox.showerror("Error", "Webcam is not initialized. Please click 'Start Webcam' first.")

    def show_delete_user_widgets(self):
        self.user_entry.grid(row=1, column=1, padx=(20, 20), pady=(10, 5), sticky="ew")
        self.add_user_button.grid(row=2, column=1, padx=(20, 20), pady=(5, 5), sticky="ew")
        self.delete_user_button.grid(row=3, column=1, padx=(20, 20), pady=(5, 20), sticky="ew")
        self.hide_delete_attendance_widgets()

    def show_delete_attendance_button(self):
        self.delete_attendance_button.grid(row=2, column=1, padx=(20, 20), pady=(5, 20), sticky="ew")
        self.hide_delete_user_widgets()

    def hide_delete_user_widgets(self):
        self.user_entry.grid_forget()
        self.add_user_button.grid_forget()
        self.delete_user_button.grid_forget()

    def hide_delete_attendance_widgets(self):
        self.delete_attendance_button.grid_forget()

    def hide_all_delete_widgets(self):
        self.hide_delete_user_widgets()
        self.hide_delete_attendance_widgets()

if __name__ == "__main__":
    app = App()
    app.mainloop()
