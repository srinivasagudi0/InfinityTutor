from core.openai_client import process_command

print('Hello! I am InfinityTutor, your AI assistant. How can I help you today? (Type "exit" or "quit" to end the session)')

while True:
    question = input("User: ")
    if question.lower() in ["exit", "quit"]:
        print("Goodbye, see you next time!")
        break
    response = process_command(question)
    print(f"InfinityTutor: {response}")
