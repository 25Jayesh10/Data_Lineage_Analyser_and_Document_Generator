from dotenv import load_dotenv
load_dotenv()
#since it is a CLI based chatbot first the user will have to select a CLIENT and the Model

def prompt_user_for_llm_client():
    """This function asks the user to select the LLM client like Gemini, OpenAI, Anthropic """
    providers = {"1": "gemini", "2": "azure openai", "3": "openai", "4": "openrouter"}
    print("\nPlease select an LLM provider to generate descriptions:")
    for key, value in providers.items():
        print(f"  {key}: {value.capitalize()}")
    
    while True:
        choice = input("Enter the number for your choice (1/2/3/4): ")
        if choice in providers:
            return providers[choice]
        else:
            print("❌ Invalid selection. Please enter 1, 2, or 3.")

def select_model_name(llm_choice):
    """This function asks the user to select the model name based on the choice of the LLM client"""
    models = {}
    menu = []
    if llm_choice == "gemini":
        models = {
            "1": "gemini-2.0-flash",
            "2": "gemini-1.5-flash"
        }
        menu = [f"  {k}: {v}" for k, v in models.items()]
    elif llm_choice == "azure openai":
        models = {
            "1": "gpt-35-turbo"
             
        }
        menu = [f"  {k}: {v}" for k, v in models.items()]
    elif llm_choice == "openai":
        models = {
            "1": "gpt-4o",
            "2": "gpt-4-turbo",
            "3": "gpt-4",
            "4": "gpt-3.5-turbo"
        }
        menu = [f"  {k}: {v}" for k, v in models.items()]
    elif llm_choice == "openrouter":
        models = {
            "1": "openrouter/gpt-4o",
            "2": "openrouter/gpt-4-turbo",
            "3": "openrouter/gemini-pro"
        }
        menu = [f"  {k}: {v}" for k, v in models.items()]
    else:
        print("Unknown LLM provider.")
        return None

    print(f"\nSelect a model for {llm_choice.capitalize()}:")
    for line in menu:
        print(line)

    while True:
        choice = input(f"Enter the number for your model choice ({'/'.join(models.keys())}): ")
        if choice in models:
            return models[choice]
        else:
            print("❌ Invalid selection. Please enter a valid number.")
