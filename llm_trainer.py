# STREAMLIT Part
import streamlit as st
import random
import re
import time

from datasets import load_dataset

dataset = load_dataset("Open-Orca/OpenOrca", split="train")


def replace_random_word(text, replacement="<BLANK>"):
    # Splitting the text into words
    words = text.split()
    # Get the indices of the words which are at least 6 letters long
    long_word_indices = [i for i, word in enumerate(words) if len(word) >= 5]
    # If there are no long words, return None and original sentence
    if not long_word_indices:
        return None, text
    # Choose a random index from the long words
    random_index = random.choice(long_word_indices)
    # Save the word to be replaced
    replaced_word = words[random_index]
    # Replace the word
    words[random_index] = replacement
    # Join the words back into a single string
    modified_text = ' '.join(words)
    # Return the replaced word and the modified text
    return replaced_word, modified_text


def pick_random_prompt():
    while True:
        # Randomly pick a data point
        datapt = random.choice(dataset)

        # If 'question' is shorter than 273 characters
        if len(datapt['question']) < 273:

            # Replace random word
            replaced_word, modified_text = replace_random_word(
                datapt['question'])
            response = datapt['response']
            # Return the results
            return replaced_word, modified_text, response


def check_guess(secret_word, guess):
    # Initialize a list of 'gray' for each letter in the guess.
    result = []
    for n in range(len(guess)):
        result.append({'letter': guess[n], 'color': 'gray'})

    # Initialize a list to keep track of which letters in the secret word have been used.
    used = [False] * len(secret_word)

    # First, check for letters in the correct position.
    for m in range(len(guess)):
        if guess[m] == secret_word[m]:
            # The letter is correct and in the correct position.
            result[m]['color'] = 'green'
            used[m] = True

    # Then, check for letters in the wrong position.
    for l in range(len(guess)):
        if result[l]['color'] == 'gray' and guess[l] in secret_word and not used[secret_word.index(guess[l])]:
            # The letter is correct but in the wrong position.
            result[l]['color'] = 'yellow'
            used[secret_word.index(guess[l])] = True

    return result


def generate_feedback_html(feedback, guess):
    # Encapsulate the feedback display in a function for reuse
    feedback_html = "<div style='display: flex;'>"
    for i, color in enumerate(feedback):
        block_color = 'lime' if color['color'] == 'green' else 'yellow' if color['color'] == 'yellow' else 'lightgray'
        feedback_html += f'<div style="display: flex; justify-content: center; align-items: center; background-color: {block_color}; width: 50px; height: 50px; margin: 5px; font-weight: bold; color: black;">{guess[i]}</div>'
    feedback_html += "</div>"
    return feedback_html


def sanitize_input(input_string):
    # Remove leading/trailing whitespace and convert to lowercase
    sanitized_input = input_string.strip().lower()
    # Ensure input only contains alphabetic characters
    if re.match("^[a-z]*$", sanitized_input):
        return sanitized_input
    else:
        return ""


def message_html(msg, color='gray'):
    return f"""
    <div style="
        display: inline-block;
        padding: 10px;
        border-radius: 10px;
        margin: 2px;
        background-color: {color};
        ">
        {msg}
    </div>
    """


def main():
    st.title('LLM Wordle')

    st.write("Guess the word in 6 tries or less!")
    # Create two columns for the Wordle game and the chat.
    game_col, chat_col = st.columns(2)
    game_col.write("## Prompt")
    # Initialize session state variables.
    if 'secret_word' not in st.session_state:
        replaced_word, modified_prompt, response = pick_random_prompt()
        st.session_state.secret_word = replaced_word
        st.session_state.prompt = modified_prompt
        st.session_state.response = response
    if 'guesses' not in st.session_state:
        st.session_state.guesses = []
    if 'feedbacks' not in st.session_state:
        st.session_state.feedbacks = []
    if 'input_key' not in st.session_state:
        st.session_state.input_key = "input"
    if 'game_over' not in st.session_state:
        st.session_state.game_over = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Handle play again logic.
    if st.session_state.game_over:
        if game_col.button("Play again? click twice"):
            st.session_state.game_over = False
            replaced_word, modified_prompt, response = pick_random_prompt()
            st.session_state.secret_word = replaced_word
            st.session_state.prompt = modified_prompt
            st.session_state.response = response
            st.session_state.guesses = []
            st.session_state.feedbacks = []
            st.session_state.chat_history = []
            st.session_state.input_key = "input" + \
                str(random.randint(0, 1000000))

    # Check if game is still ongoing.
    if not st.session_state.game_over:
        # Allow the user to enter a guess.
        game_col.write(st.session_state.prompt)
        guess = game_col.text_input(
            "Enter your guess", key=st.session_state.input_key)
        guess = sanitize_input(guess)  # Sanitize the user input

        chat_col.markdown("## Response")
        chat_col.write(st.session_state.response)

        # Check the guess.
        if guess in st.session_state.guesses:
            game_col.write("You already guessed that word.")
        elif len(guess) == 0:
            game_col.write("Please enter a word.")
        else:
            feedback = check_guess(st.session_state.secret_word, guess)
            st.session_state.guesses.append(guess)
            st.session_state.feedbacks.append(feedback)
            st.session_state.input_key = "input" + \
                str(random.randint(0, 1000000))

        if guess == st.session_state.secret_word:
            game_col.write("You win!")
            st.session_state.game_over = True
            if game_col.button("Next"):
                pass
        elif len(st.session_state.guesses) >= 6:
            game_col.write("You lost! the word was " +
                           st.session_state.secret_word)
            st.session_state.game_over = True
            if game_col.button("Next"):
                pass

        # Display previous feedbacks
        for past_feedback, past_guess in zip(st.session_state.feedbacks, st.session_state.guesses):
            past_feedback_html = generate_feedback_html(
                past_feedback, past_guess)
            game_col.markdown(past_feedback_html, unsafe_allow_html=True)

        for message in st.session_state.chat_history:
            chat_col.markdown(message_html(message, 'purple'),
                              unsafe_allow_html=True)


if __name__ == "__main__":
    main()
