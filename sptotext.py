import speech_recognition as sr
import threading
import time

class SpeechCapture:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.letters = []
        self.running = True

    def recognize_speech(self):
        with sr.Microphone() as source:
            while self.running:
                try:
                    audio = self.recognizer.listen(source)
                    result = self.recognizer.recognize_google(audio)
                    print(f"You said: {result}")
                    if len(result) == 1 and result.isalpha():
                        self.letters.append(result.upper())
                except sr.UnknownValueError:
                    print("Sorry, could not understand the audio.")
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")

    def start_capture(self):
        capture_thread = threading.Thread(target=self.recognize_speech)
        capture_thread.start()

    def stop_capture(self):
        self.running = False

def main():
    capture = SpeechCapture()
    capture.start_capture()

    input("Press Enter to stop capturing...")
    capture.stop_capture()
    print("Recognized Letters:", capture.letters)

if __name__ == "__main__":
    main()
