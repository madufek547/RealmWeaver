
from flask import Flask, render_template, request, redirect, url_for
import requests
import openai
import os
from dotenv import load_dotenv
import dotenv
import func.dice as dice
import random
app = Flask(__name__)

load_dotenv(override=True)
api_key = dotenv.get_key(".env", "OPENAI_API_KEY")
print(api_key)
ABILITIES = {
    'str': 'Strength',
    'dex': 'Dexterity',
    'con': 'Constitution',
    'int': 'Intelligence',
    'wis': 'Wisdom',
    'cha': 'Charisma'
}

def calculate_modifier(ability_scores, ability):
    if ability not in ability_scores:
        return 0
    return (ability_scores[ability] - 10) // 2





def get_class_hit_dice(char_class):
    """
    Given a character class, returns the corresponding hit dice.
    """
    hit_dice_map = {
        "Barbarian": 12,
        "Bard": 8,
        "Cleric": 8,
        "Druid": 8,
        "Fighter": 10,
        "Monk": 8,
        "Paladin": 10,
        "Ranger": 10,
        "Rogue": 8,
        "Sorcerer": 6,
        "Wizard": 6
    }

    if char_class in hit_dice_map:
        return hit_dice_map[char_class]
    else:
        return None


def roll_ability_scores():
    # Create an empty dictionary to hold ability scores
    ability_scores = {}
    # Generate six ability scores using 4d6 drop lowest method
    for ability in ['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma']:
        score = dice.roll_dice(4, 6)
        score.remove(min(score))
        ability_scores[ability] = int(sum(score))
    print(f"Generated ability scores: {ability_scores}")
    return ability_scores





@app.route('/campaign', methods=['GET', 'POST'])
def campaign():
    if request.method == 'POST':
        campaign_name = request.form['campaign_name']
        num_players = request.form['num_players']
        format = request.form['format']
        length = request.form['length']
        campaign_type = request.form['type']
        return redirect(url_for('confirm', campaign_name=campaign_name, num_players=num_players, format=format, length=length))
    return render_template('campaign.html')

@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    if request.method == 'POST':
        campaign_name = request.form['campaign_name']
        num_players = request.form['num_players']
        length = request.form['length']
        campaign_type = request.form['type']
        format = request.form['format']
        prompt = generate_prompt(campaign_name, num_players, format, length, campaign_type)
        campaign = generate_campaign(prompt)
        return render_template('confirm.html', prompt=prompt, campaign=campaign)
    else:
        return redirect(url_for('campaign'))

@app.route('/charactersheet', methods=['GET', 'POST'])
def character_sheet():
    if request.method == 'POST':
        # Get character information from form
        name = request.form['name']
        race = request.form['race']
        char_class = request.form['class']
        age = request.form['age']
        gear = request.form['gear']
        weapons = request.form['weapons']
        spells = request.form['spells']
        extra_info = request.form['extra_info']
        # Generate ability scores
        ability_scores = roll_ability_scores()
        hit_dice = get_class_hit_dice(char_class)
        if hit_dice is None:
            hit_dice = 8
        # Calculate HP based on hit dice and constitution modifier
        hit_dice_value = dice.roll_dice(1, hit_dice)
        con_mod = calculate_modifier(ability_scores, 'Constitution')


        hp = sum(hit_dice_value) + con_mod

        # Generate GPT response for background, motivation, and alignment
        prompt = f"Generate a backstory, motivation, and alignment for a {race} {char_class} named {name}."
        response = generate_gpt_response(prompt)

        # Render character sheet template with generated data
        return render_template('confirmcharacter.html',
                               name=name,
                               race=race,
                               char_class=char_class,
                               age=age,
                               gear=gear,
                               weapons=weapons,
                               spells=spells,
                               str_score=ability_scores['Strength'],
                               dex_score=ability_scores['Dexterity'],
                               con_score=ability_scores['Constitution'],
                               int_score=ability_scores['Intelligence'],
                               wis_score=ability_scores['Wisdom'],
                               cha_score=ability_scores['Charisma'],
                               str_mod=calculate_modifier(ability_scores,'Strength'),
                               dex_mod=calculate_modifier(ability_scores, 'Dexterity'),
                               con_mod=con_mod,
                               int_mod=calculate_modifier(ability_scores, 'Intelligence'),
                               wis_mod=calculate_modifier(ability_scores, 'Wisdom'),
                               cha_mod=calculate_modifier(ability_scores, 'Charisma'),
                               hp=hp,
                               extra_info=extra_info,
                               response=response)
    else:
        return render_template('charactersheet.html')




def generate_campaign(prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )

    campaign = completion['choices'][0]['message']['content']
    return campaign

def generate_gpt_response(prompt):
    """
    Given a prompt, returns a GPT-3 generated response using the specified model engine.
    """
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    message = completion['choices'][0]['message']['content']
    # Remove newline characters and return the response
    return message

@app.route('/confirmcharacter', methods=['POST'])
def confirmcharacter():
    name = request.form['name']
    age = request.form['age']
    race = request.form['race']
    char_class = request.form['class']
    gear = request.form['gear']
    weapons = request.form['weapons']
    spells = request.form['spells']
    extra_info = request.form['extra_info']
    scores = {
        "Strength": 0,
        'Dexterity': 0,
        'Constitution' : 0,
        'Intelligence' : 0,
        'Wisdom' : 0,
        'Charisma': 0
    }
    # Roll ability scores and calculate modifiers
    scores = roll_ability_scores()
    modifiers = {}
    for i, score in scores:
        modifiers[scores[i]] = calculate_modifier(score)

    # Generate HP based on constitution modifier and class hit dice
    con_mod = modifiers['Constitution']
    hit_dice = get_class_hit_dice(char_class)
    hp = f"{hit_dice} + {con_mod}"

    # Generate character background, motivation, and alignment using GPT-3
    prompt = f"Generate a background, motivation, and alignment for a {race} {char_class} named "#{name}
    + "."
    response = generate_gpt_response(prompt)

    # Render the confirmation page with all the information
    return render_template('confirmcharacter.html', name=name, age=age, race=race, char_class=char_class, gear=gear, weapons=weapons, spells=spells, abilities=scores, modifiers=modifiers, hp=hp, response=response, extra_info=extra_info)


@app.route('/')
def index():
    return render_template('index.html')


def generate_prompt(campaign_name, num_players, format, length, campaign_type):
    prompt = f"Create a {format} DND/Pathfinder-like campaign called '{campaign_name}' for {num_players} players in which each session(s) lasts {length} hours. The campaign should include a variety of encounters and NPCs for the players to interact with and follow the theme given. This is the description given by the DM:'{campaign_type}."
    return prompt


if __name__ == '__main__':
    app.run(debug=True)
