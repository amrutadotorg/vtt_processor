#!/usr/bin/env python3
import webvtt
import sys
import re
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinterdnd2 as tkdnd


class VTTProcessorApp:
    def __init__(self, master):
        self.master = master
        master.title("VTT File Processor")
        master.geometry("600x500")

        # Tracking dropped files
        self.dropped_files = []

        # Style
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Arial", 10))
        self.style.configure("TButton", font=("Arial", 10))

        # Drag and Drop Setup
        self.master.drop_target_register(tkdnd.DND_FILES)
        self.master.dnd_bind("<<Drop>>", self.handle_drop)

        # Create UI Elements
        self.create_widgets()

    def create_widgets(self):
        # Drag and Drop Area
        self.drop_frame = tk.Frame(
            self.master,
            width=500,
            height=200,
            bg="light gray",
            borderwidth=2,
            relief=tk.RIDGE,
        )
        self.drop_frame.pack(pady=20, padx=20, fill=tk.X)
        self.drop_frame.pack_propagate(False)

        self.drop_label = tk.Label(
            self.drop_frame,
            text="Drag and Drop VTT and Text Files Here",
            bg="light gray",
            font=("Arial", 12),
        )
        self.drop_label.pack(expand=True)

        # Operation Buttons Frame
        button_frame = tk.Frame(self.master)
        button_frame.pack(pady=10)

        # Buttons for different operations
        ttk.Button(
            button_frame, text="Extract VTT Text", command=self.extract_vtt_text_gui
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            button_frame, text="Replace VTT Text", command=self.replace_vtt_text_gui
        ).pack(side=tk.LEFT, padx=5)

        # Result Display
        self.result_text = tk.Text(self.master, height=10, width=70, wrap=tk.WORD)
        self.result_text.pack(pady=10, padx=20, fill=tk.X)

    def handle_drop(self, event):
        """Handle file drop event"""
        self.dropped_files = self.master.tk.splitlist(event.data)
        if not self.dropped_files:
            return

        # Categorize dropped files
        vtt_files = [f for f in self.dropped_files if f.lower().endswith(".vtt")]
        text_files = [f for f in self.dropped_files if f.lower().endswith(".txt")]

        # If we have both VTT and text files, prompt for replacement
        if vtt_files and text_files:
            self.prompt_vtt_replacement(vtt_files[0], text_files[0])
        elif len(vtt_files) == 1:
            self.process_vtt_file(vtt_files[0])
        elif len(text_files) == 1:
            self.process_text_file(text_files[0])
        else:
            messagebox.showinfo("Unsupported Files", "Please drop .vtt or .txt files")

    def prompt_vtt_replacement(self, vtt_file, text_file):
        """Prompt user to replace VTT text with dropped text file"""
        dialog = tk.Toplevel(self.master)
        dialog.title("Replace VTT Text")
        dialog.geometry("300x200")

        tk.Label(
            dialog, text="Replace VTT text with dropped text file?", wraplength=250
        ).pack(pady=10)

        def do_replace():
            try:
                # Always clean the text file during replacement
                output = os.path.splitext(vtt_file)[0] + "_replaced.vtt"
                replace_vtt_text(vtt_file, text_file, output, clean_text=True)
                self.update_result_text(
                    f"Replaced text in {vtt_file} with cleaned {text_file}"
                )
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        def cancel():
            dialog.destroy()

        ttk.Button(dialog, text="Replace", command=do_replace).pack(pady=5)
        ttk.Button(dialog, text="Cancel", command=cancel).pack(pady=5)

    def process_vtt_file(self, vtt_file):
        """Guess best operation for VTT file"""
        dialog = tk.Toplevel(self.master)
        dialog.title("VTT File Action")
        dialog.geometry("300x200")

        def do_extract():
            output = os.path.splitext(vtt_file)[0] + "_text.txt"
            self.extract_vtt_text_single(vtt_file, output)
            dialog.destroy()

        def do_replace():
            text_file = filedialog.askopenfilename(
                title="Select Replacement Text File",
                filetypes=[("Text Files", "*.txt")],
            )
            if text_file:
                output = os.path.splitext(vtt_file)[0] + "_replaced.vtt"
                self.replace_vtt_text_single(vtt_file, text_file, output)
            dialog.destroy()

        tk.Label(dialog, text="Choose an action for VTT file:").pack(pady=10)
        ttk.Button(dialog, text="Extract Text", command=do_extract).pack(pady=5)
        ttk.Button(dialog, text="Replace Text", command=do_replace).pack(pady=5)

    def process_text_file(self, text_file):
        """Guess best operation for text file"""
        output = os.path.splitext(text_file)[0] + "_cleaned.txt"
        self.clean_text_file_single(text_file, output)

    def extract_vtt_text_single(self, vtt_file, output_file):
        """Extract text from a single VTT file"""
        try:
            actual_output_files = extract_vtt_text(vtt_file, output_file)

            # Handle both single file and multiple file scenarios
            if isinstance(actual_output_files, list):
                # Multiple files scenario
                output_message = f"Extracted text from {vtt_file}, split into {len(actual_output_files)} files:\n"
                output_message += "\n".join(actual_output_files)
            else:
                # Single file scenario
                output_message = (
                    f"Extracted text from {vtt_file} to {actual_output_files}"
                )

            self.update_result_text(output_message)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clean_text_file_single(self, text_file, output_file):
        """Clean a single text file"""
        try:
            clean_text_file(text_file, output_file)
            self.update_result_text(f"Cleaned text file: {text_file}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def replace_vtt_text_single(self, vtt_file, text_file, output_file):
        """Replace text in a single VTT file"""
        try:
            # Always clean the text file during replacement
            replace_vtt_text(vtt_file, text_file, output_file, clean_text=True)
            self.update_result_text(
                f"Replaced text in {vtt_file} with cleaned {text_file}"
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_result_text(self, message):
        """Update the result text area"""
        self.result_text.insert(tk.END, message + "\n")
        self.result_text.see(tk.END)

    def extract_vtt_text_gui(self):
        """GUI method to extract VTT text"""
        vtt_file = filedialog.askopenfilename(
            title="Select VTT File", filetypes=[("VTT Files", "*.vtt")]
        )
        if vtt_file:
            output_file = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("Text Files", "*.txt")]
            )
            if output_file:
                self.extract_vtt_text_single(vtt_file, output_file)

    def replace_vtt_text_gui(self):
        """GUI method to replace VTT text"""
        vtt_file = filedialog.askopenfilename(
            title="Select VTT File", filetypes=[("VTT Files", "*.vtt")]
        )
        if vtt_file:
            text_file = filedialog.askopenfilename(
                title="Select Replacement Text File",
                filetypes=[("Text Files", "*.txt")],
            )
            if text_file:
                output_file = filedialog.asksaveasfilename(
                    defaultextension=".vtt", filetypes=[("VTT Files", "*.vtt")]
                )
                if output_file:
                    replace_vtt_text(vtt_file, text_file, output_file, clean_text=True)
                    self.update_result_text(f"Replaced text in {vtt_file}")


def clean_text_file(input_file_path, output_file_path=None):
    """
    Cleans a text file by removing line numbers, extra spaces, &nbsp; entities,
    and replacing multiple consecutive spaces with a single space.

    Args:
        input_file_path (str): Path to the input text file
        output_file_path (str, optional): Path where the cleaned text will be saved.
                                         If None, returns the cleaned lines.

    Returns:
        list or None: If output_file_path is None, returns a list of cleaned lines.
                     Otherwise, returns None after saving to file.
    """
    # Read the input file
    with open(input_file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # Clean each line
    cleaned_lines = []
    for line in lines:
        # First, remove &nbsp; entities
        line = line.replace("&nbsp;", " ")

        # Remove line numbers (pattern like "200." or "201.") and leading whitespace
        cleaned_line = re.sub(r"^\s*\d+\.\s*", "", line.strip())

        # Replace multiple consecutive spaces with a single space
        cleaned_line = re.sub(r" {2,}", " ", cleaned_line)

        # Only add non-empty lines
        if cleaned_line:
            cleaned_lines.append(cleaned_line)

    # If an output file path is provided, save the cleaned lines
    if output_file_path:
        with open(output_file_path, "w", encoding="utf-8") as file:
            for line in cleaned_lines:
                file.write(f"{line}\n")
            print(f"Successfully cleaned text file and saved to: {output_file_path}")
        return None

    # Otherwise, return the cleaned lines
    return cleaned_lines


def extract_vtt_text(vtt_file_path, output_file_path, max_lines=300):
    """
    Extracts text content from a VTT file without timestamps and saves it to text file(s).
    Splits into multiple files if number of lines exceeds max_lines.

    Args:
        vtt_file_path (str): Path to the input VTT file
        output_file_path (str): Path where the text content will be saved
        max_lines (int): Maximum number of lines per output file
    """
    try:
        # Parse the VTT file
        vtt = webvtt.read(vtt_file_path)
        # Extract and process text from each caption
        extracted_lines = []
        for caption in vtt.captions:
            # Replace newlines with spaces to merge multi-line captions into a single line
            merged_text = " ".join(caption.text.split("\n"))
            # Remove &nbsp; entities
            merged_text = merged_text.replace("&nbsp;", " ")
            # Replace multiple consecutive spaces with a single space
            merged_text = re.sub(r" {2,}", " ", merged_text)
            # Only add non-empty lines
            if merged_text.strip():
                extracted_lines.append(merged_text)

        # Determine output file paths
        if output_file_path:
            # Get the directory and base filename
            file_dir = os.path.dirname(output_file_path)
            base_filename = os.path.basename(output_file_path)
            base_name, file_ext = os.path.splitext(base_filename)

            # Split into multiple files if needed
            output_files = []
            if len(extracted_lines) > max_lines:
                # Calculate number of files needed
                num_files = (len(extracted_lines) + max_lines - 1) // max_lines

                for i in range(num_files):
                    # Calculate start and end indices for this file
                    start_idx = i * max_lines
                    end_idx = min((i + 1) * max_lines, len(extracted_lines))

                    # Calculate total lines in each file
                    current_file_lines = end_idx - start_idx

                    # Create filename with file number and total lines
                    current_filename = f"{base_name}_{i + 1}of{num_files}_{current_file_lines}lines{file_ext}"
                    current_filepath = os.path.join(file_dir, current_filename)

                    # Write subset of lines to file, removing trailing newline
                    with open(current_filepath, "w", encoding="utf-8") as text_file:
                        text_file.write(
                            "\n".join(extracted_lines[start_idx:end_idx]).rstrip()
                        )

                    output_files.append(current_filepath)

                print(
                    f"Successfully split {len(extracted_lines)} lines from VTT file into {num_files} files"
                )
                return output_files

            # If no splitting needed
            current_file_lines = len(extracted_lines)
            full_output_path = os.path.join(
                file_dir, f"{base_name}_{current_file_lines}lines{file_ext}"
            )
            # Write lines to file, removing trailing newline
            with open(full_output_path, "w", encoding="utf-8") as text_file:
                text_file.write("\n".join(extracted_lines).rstrip() + "\n")

            print(
                f"Successfully extracted {len(extracted_lines)} lines from VTT file to: {full_output_path}"
            )
            return full_output_path

        # If no output path provided, return the lines
        return extracted_lines

    except Exception as e:
        raise Exception(f"Error extracting text from VTT: {e}")


def replace_vtt_text(vtt_file_path, text_file_path, output_file_path, clean_text=False):
    """
    Replaces the text content in a VTT file with text from a separate text file
    using the webvtt-py library. Skips empty lines in the text file.

    Args:
        vtt_file_path (str): Path to the input VTT file
        text_file_path (str): Path to the text file with replacement content
        output_file_path (str): Path where the modified VTT file will be saved
        clean_text (bool): Whether to clean the text file before using it
    """
    # If cleaning is requested, clean the text file first
    if clean_text:
        replacement_lines = clean_text_file(text_file_path)
    else:
        # Read the replacement text, skipping empty lines
        with open(text_file_path, "r", encoding="utf-8") as text_file:
            replacement_lines = [
                line.strip() for line in text_file.readlines() if line.strip()
            ]

    # Parse the VTT file
    vtt = webvtt.read(vtt_file_path)

    # Check if we have the right number of replacement lines
    if len(replacement_lines) != len(vtt.captions):
        raise ValueError(
            f"Number of non-empty lines in text file ({len(replacement_lines)}) "
            f"doesn't match number of captions in VTT file ({len(vtt.captions)})"
        )

    # Replace the text for each caption
    for i, caption in enumerate(vtt.captions):
        caption.text = replacement_lines[i]

    # Save the modified VTT file
    vtt.save(output_file_path)
    print(
        f"Successfully created new VTT file with replaced text at: {output_file_path}"
    )


def main():
    """Start the GUI application"""
    root = tkdnd.Tk()
    app = VTTProcessorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

