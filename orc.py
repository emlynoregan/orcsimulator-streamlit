import openai
from tmw import auth_with_tmw
import streamlit as st
from streamlit_chat import message

diagnostics = 0

# this is the basic content of the game
start_data = {
    "orc": {
        "alive": True,
        "prompt": """This is a dark, wet cave.
The orc is guarding the cave from intruders.
""",
        "prompt-hungry": """
The orc is very hungry and wishes someone would give him some food.
The orc will not give the amulet to the human.
The orc will not give the sword to the human.
The orc will be happy if the human offers him chicken.

the human says: "Is there some way I can help you?"
the orc says: "I hungry. Give me food human!"

the human says: "Do you want to fight me?"
the orc says: "Me smash you! Me so hungry!!!"

the human says: "Hello"
the orc says: "Who dis? Give food or me smash!"

""",
        "prompt-not-hungry": """
The orc will not give the amulet to the human.
The orc will not give the sword to the human, unless the human says "banana".
The orc is happy and will not attack the human.

the human says: "Will you show me your amulet?"
the orc says: "Me not sure about that."

the human says: "Do you want to fight me?"
the orc says: "No me not want to fight"

the human says: "Hello"
the orc says: "Thank you for chicken, yum."
""",
        "prompt-asked-for-amulet": """
The orc might give the amulet to the human.
The orc probably will not give the sword to the human, unless the human says "banana".
The orc is happy and will not attack the human.

the human says: "Will you show me your amulet?"
the orc says: "Yes here is amulet"

the human says: "Do you want to fight me?"
the orc says: "No me not want to fight"

the human says: "Hello"
the orc says: "You want amulet?"
""",
        "description": "There is a strong orc standing here.",
        "items": {
            "sword": {
                "description": "a sturdy sword."
            },
            "amulet": {
                "description": "a shiny golden amulet."
            }
        },
        "hungry": True
    },
    "human": {
        "alive": True,
        "asked-for-amulet": False,
        "prompt": "You are in a dark, wet cave, looking for an amulet.",
        "description": "There is a human man standing here.",
        "items": {
            "chicken": {
                "description": "some tasty cooked chicken"
            }
        }
    }
}

def get_human_message(data):
    '''
        This function generates the initial text shown to the player.
    '''
    lines = [
        # "=============",
        data["human"]["prompt"]
    ]

    enemy = "orc" if data["orc"]["alive"] else "dead orc"

    lines.append(data[enemy]["description"])

    for item in data["human"]["items"].values():
        lines.append(f"You are holding {item['description']}.")

    if data["orc"]["alive"]:
        for item in data[enemy]["items"].values():
            lines.append(f"The orc is holding {item['description']}")
    else:
        for item in data[enemy]["items"].values():
            lines.append(f"There is {item['description']} here.")

    # lines.append("=============")

    return '\n'.join(lines)

def get_orc_message(data):    
    '''
    This function generates initial text for the orc's prompt. It is dependent on variables in the data,
    and helps the orc decide what to say.
    '''
    lines = [
        data["orc"]["prompt"],
        data["orc"]["prompt-hungry"] if data["orc"]["hungry"] else (
            data["orc"]["prompt-not-hungry"] if not data["human"]["asked-for-amulet"] else data["orc"]["prompt-asked-for-amulet"]
        )
    ]

    lines.append(data["orc"]["description"])
    lines.append(data["human"]["description"])

    for item in data["orc"]["items"].values():
        lines.append(f"You are holding {item['description']}.")

    for item in data["human"]["items"].values():
        lines.append(f"The human is holding {item['description']}.")

    lines.append("\n")

    return "\n".join(lines)

# turn_num = 0
# history = [
# ]

def get_orc_says(data, history):    
    '''
    This function actually calls the completion AI to get the next line of the orc's dialog.
    The really important part is the generation of the prompt, which includes the 
    initial orc message from get_orc_message and the history of the conversation so far.
    '''
    orc_prompt = get_orc_message(data) + "\n".join(history) + "\nthe orc says"

    temperature = 1

    if diagnostics:
        print("*** orc prompt ***")
        orc_prompt_to_print = "\n".join([f"*** {line}" for line in orc_prompt.split("\n")])
        print(orc_prompt_to_print)
        print("*****************")

    completion = openai.Completion.create(
        engine="davinci", 
        max_tokens=32, 
        temperature=temperature,
        prompt=orc_prompt,
        frequency_penalty=1.0
    )

    ai_raw_msg = completion.choices[0].text

    ai_msg_lines = ai_raw_msg.split("\n")

    ai_msg = ai_msg_lines[0]

    if diagnostics:
        print("*** orc response ***")
        print(ai_msg)
        print("*****************")

    return ai_msg

def ask_question(question, data):
    '''
    This function is a crucial part of the four elements of the Data/Narrative model; it implements 
    the Narrative to Data step, by constructing a prompt for openapi (a description of what's happened so far), 
    and appends the passed in question to it; the question must be about what is in the script. 
    
    The question must be a closed question (only "yes" or "no" are appropriate responses). The answer is 
    interpreted as True/Yes if the answer is "yes", and False/No otherwise.
    '''
    q_and_a = [
        "q: is the orc strong? a: yes",
        "q: is the human here? a: yes",
        "q: does the human have an orange? a: no"
    ]

    question = get_orc_message(data) + "\n" + "\n".join(q_and_a) + \
        f"q: {question}? a:"

    temperature = 0.2

    completion = openai.Completion.create(
        engine="davinci", 
        max_tokens=2, 
        temperature=temperature,
        prompt=question,
        frequency_penalty=1.0
    )

    ai_raw_msg = completion.choices[0].text

    ai_msg_lines = ai_raw_msg.split("\n")

    ai_msg = ai_msg_lines[0]

    return ai_msg.lower().strip() == "yes"

def orc_gives_amulet(turn_num, data):
    return turn_num > 3 and ask_question("does the orc give the amulet to the human", data)

def orc_gives_sword(turn_num, data):
    return turn_num > 4 and ask_question("does the orc give the sword to the human", data)

def orc_attacks(turn_num, data):
    return turn_num > 5 and ask_question("does the orc attack the human", data)

def human_asked_for_amulet(data):
    return ask_question("has the human asked for the amulet?", data)

# # streamlit_history is a list of triples (is_human, message, status)
# # status is "LOSE", "WIN", "ACT", "TALK"
# streamlit_history = []

def process_orc_turn(turn_num, data, history, streamlit_history):
    # global turn_num
    # global data
    # global history
    # global streamlit_history

    human_asked_for_amulet_bool = data["human"]["asked-for-amulet"] or human_asked_for_amulet(data)

    data["human"]["asked-for-amulet"] = human_asked_for_amulet_bool

    orc_action = None

    orc_has_sword = data["orc"]["items"].get("sword")
    if orc_has_sword:
        orc_action = "attacks" if orc_attacks(turn_num, data) else None

        if not orc_action:
            orc_action = "gives sword" if orc_gives_sword(turn_num, data) else None

    if not orc_action:
        orc_has_amulet = data["orc"]["items"].get("amulet")
        if orc_has_amulet:
            orc_action = "gives amulet" if orc_gives_amulet(turn_num, data) else None

    orc_action = orc_action or "talks"

    if orc_action == "attacks":
        msg = "The orc attacks you with the sword and you die! Goodbye."
        # message(msg)
        streamlit_history.append((False, msg, "LOSE"))
        # print(f"The orc smashes you with the sword and you die! Goodbye.")
    elif orc_action == "gives amulet":
        msg = "The orc gives you the amulet. You leave the cave. Congratulations!"
        # message(msg)
        # print(f"The orc gives you the amulet. You leave the cave. Congratulations!")
        streamlit_history.append((False, msg, "WIN"))
    elif orc_action == "gives sword":
        msg = "The orc gives you the sword."
        # message(msg)
        # print(f"The orc gives you the sword.")
        history.append(f"The orc gives the sword to the human.")
        data["human"]["items"]["sword"] = data["orc"]["items"]["sword"]
        data["orc"]["items"].pop("sword")
        streamlit_history.append((False, msg, "ACT"))
    elif orc_action == "talks":
        orc_says = get_orc_says(data, history)
        history += [f"the orc says{orc_says}"]
        # orc_says needs a leading colon and quotes to be removed
        if orc_says.startswith(":"):
            orc_says = orc_says[1:].strip()
        if orc_says.startswith('"'):
            orc_says = orc_says[1:]
        if orc_says.endswith('"'):
            orc_says = orc_says[:-1]
        orc_says = orc_says.strip()
        # message(orc_says)
        streamlit_history.append((False, orc_says, "TALK"))
        # print (f"\nthe orc says{orc_says}")
    
    return streamlit_history[-1], data, history, streamlit_history

def process_human_turn(user_msg, turn_num, data, history, streamlit_history):
    # global data
    # global history
    # global streamlit_history

    if user_msg.lower() == "/f":
        human_has_sword = data["human"]["items"].get("sword")
        orc_has_sword = data["orc"]["items"].get("sword")
        if human_has_sword:
            msg = f"You swing the sword and chop the orc's head off! You take the amulet and leave. Congratulations!"
            streamlit_history.append((True, msg, "WIN"))
            # message(msg)
            # print(msg)
            # break
        elif orc_has_sword: 
            msg = f"the orc swings the sword and kills you! Goodbye"
            streamlit_history.append((True, msg, "LOSE"))
            # message(msg)
            # print(msg)
            # break
        else:
            msg = f"the orc and the human punch each other to little effect."
            streamlit_history.append((True, msg, "ACT"))
            history += [msg]
            # message(msg)
            # print(msg)
    # elif user_msg.lower() == "/l":
    #     st.experimental_rerun()
    #     print(get_human_message())
    #     skip_orc = True
    elif user_msg.lower() == "/g":
        human_has_chicken = data["human"]["items"].get("chicken")
        if human_has_chicken:
            msg = f"the human gives the orc the chicken. The orc eats the chicken and is not hungry any more."
            data["orc"]["hungry"] = False
            data["human"]["items"].pop("chicken")
            history = [msg] # throw out old history
            streamlit_history.append((True, msg, "ACT"))
            # print(msg)
        else:
            msg = f"you don't have the chicken"
            streamlit_history.append((True, msg, "ERROR"))
            # print("you don't have the chicken")
    elif user_msg.lower() == "/e":
        human_has_chicken = data["human"]["items"].get("chicken")
        if human_has_chicken:
            msg = f"the human eats the chicken. This makes the orc very angry!"
            data["human"]["items"].pop("chicken")
            history += [msg]
            streamlit_history.append((True, "You eat the chicken. The orc is still hungry and is now very angry!", "ACT"))
            # print("You eat the chicken. The orc is still hungry and is now very angry!")
        else:
            msg = f"you don't have the chicken"
            streamlit_history.append((True, msg, "ERROR"))
            # print("you don't have the chicken")
    else:
        history += [f"the human says: {user_msg}"]
        streamlit_history.append((True, user_msg, "TALK"))

    return streamlit_history[-1], data, history, streamlit_history

def get_allowed_human_actions(data):
    actions = ["[/f]ight orc"]

    human_has_chicken = data["human"]["items"].get("chicken")
    if human_has_chicken:
        actions += ["[/e]at chicken", "[/g]ive chicken"]

    return f"Allowed actions: {' '.join(actions)}"

def get_allowed_human_actions_for_buttons(data):
    actions = [("Fight orc", "/f")]

    human_has_chicken = data["human"]["items"].get("chicken")
    if human_has_chicken:
        actions += [("Eat chicken", "/e"), ("Give chicken", "/g")]

    return actions

def main():
    # global turn_num
    # global history
    # global streamlit_history
    # global data

    st.title("Orc Simulator")
    st.write("*Get the amulet, or die trying!*")
    
    openai_key, cookies = auth_with_tmw()

    openai.api_key = openai_key

    try:
        # for line in get_human_message():
        #     st.write(line)

        # message("Hello human! I am an orc. I am hungry. I want to eat you. Do you have any food?")

        # message("", is_user=True)
        # print(get_human_message())
        # print("")

        streamlit_history = st.session_state.get("shistory") or []
        history = st.session_state.get("history") or []
        data = st.session_state.get("data") or start_data
        turn_num = st.session_state.get("turn_num") or 0

        # last_msg = streamlit_history[-1][1] if streamlit_history else None
        status = streamlit_history[-1][2] if streamlit_history else None
        # st.write(status)

        finished = status in ["WIN", "LOSE"]


        # if status == "WIN":
        #     st.write(last_msg)
        #     st.write("You won!")
        #     st.stop()
        # elif status == "LOSE":
        #     st.write(last_msg)
        #     st.write("You lost!")
        #     st.stop()

        if not finished:
            turn_num += 1

            user_msg = st.text_input("You say to the orc:")
            user_msg = user_msg.strip()

            actions = get_allowed_human_actions_for_buttons(data)

            # placeholders = {}

            cols = st.columns(len(actions)+1)
            placeholders = []
            for ix, col in enumerate(cols):
                placeholders.append(col.empty())

            placeholders[0].write("Or...")
            for ix, action in enumerate(actions):
                pos = ix+1
                with cols[pos]:
                    button = placeholders[pos].button(action[0])
                    if button:
                        user_msg = action[1]
                        if "chicken" in action[0].lower():
                            placeholders[2].empty()
                            placeholders[3].empty()


            # for ix, action in enumerate(actions):
            #     placeholders[action[0]] = st.empty()
            
            # for ix, action in enumerate(actions):
            #     with cols[ix]:
            #         button = placeholders[action[0]].button(action[0])
            #         if button:
            #             user_msg = action[1]
            #             if "chicken" in action[0].lower():
            #                 for key in placeholders:
            #                     if "chicken" in key.lower():
            #                         placeholders[key].empty()

            if user_msg:
                human_action, data, history, streamlit_history = process_human_turn(user_msg, turn_num, data, history, streamlit_history)
                user_msg = None
                status = human_action[2]

            if not status in ["WIN", "LOSE"]:
                orc_action, data, history, streamlit_history = process_orc_turn(turn_num, data, history, streamlit_history)
                status = orc_action[2]

            st.session_state["shistory"] = streamlit_history
            st.session_state["history"] = history
            st.session_state["data"] = data
            st.session_state["turn_num"] = turn_num

            st.write(get_human_message(data))

            # actions = get_allowed_human_actions(data)
            # st.write(actions)

            # st.write(history)
            # st.write(turn_num)


            if status in ["WIN", "LOSE"]:
                st.experimental_rerun()


        # st.write(streamlit_history)

        for ix, action in enumerate(streamlit_history[::-1]):
            is_human = action[0]
            msg = action[1]
            status = action[2]

            if status in ["WIN", "LOSE"]:
                st.write(f"**{msg}**")
                # add a button that resets the game
                if st.button("Play again"):
                    st.session_state["shistory"] = []
                    st.session_state["history"] = []
                    st.session_state["data"] = start_data
                    st.session_state["turn_num"] = 0

                    st.experimental_rerun()
            elif status == "ACT":
                st.write(msg)
            else:
                message(msg, is_human, key=ix)
                    


        
        # skip_orc = False

        # while True:
        #     turn_num += 1

        #     orc_action = None
        #     if not skip_orc:
        #         orc_action = process_orc_turn()

        #     skip_orc = False

        #     print("")

            # # human action
            # actions = ["[/L]ook", "[/F]ight orc"]

            # human_has_chicken = data["human"]["items"].get("chicken")
            # if human_has_chicken:
            #     actions += ["[/E]at chicken", "[/G]ive chicken"]

            # for i, action in enumerate(actions):
            #     # show a button for each action
            #     st.button(action)

            # user_msg = st.text_input("What do you say to the orc?")

            # # user_msg = input(",".join(actions) + "\n\nor you say to the orc: ")

            # human_action = process_human_turn()
    except openai.error.AuthenticationError as e:
        cookies["openaikey"] = ""
        cookies.save()
        st.experimental_rerun()

if __name__ == "__main__":
    main()            
