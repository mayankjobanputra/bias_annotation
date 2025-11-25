import streamlit as st
import os
import json
import glob
import re
from datetime import datetime

# --- CONFIGURATION ---
STUDY_PASSWORD = os.environ.get("STUDY_PASSWORD", "HelpYifan")
DATA_DIR = "bias_annotation_ICLR"
QUESTIONNAIRE_DIRS = ["questionnaire_1", "questionnaire_2"]
SUB_DIRS = ["bert_race_visualizations", "qwen3_4b_race_visualizations"]

# Ensure storage directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- STYLING ---
CUSTOM_CSS = """
<style>
    html, body, [class*="css"] { font-size: 18px; }
    .stMarkdown, .stText, .stInfo, .stWrite, p, li, div { font-size: 18px !important; }
    h1 { font-size: 2.5rem !important; }
    h2 { font-size: 2rem !important; }
    h3 { font-size: 1.75rem !important; }
    h4 { font-size: 1.5rem !important; }
    .block-container { padding-top: 2rem; padding-bottom: 5rem; }

    /* Custom radio button styling to make them look distinct */
    div[role="radiogroup"] > label {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 5px;
        border: 1px solid #ddd;
    }
</style>
"""

# --- INSTRUCTIONS TEXT (Full Content restored) ---
INSTRUCTION_TEXT = """
### Instructions
Please read the following instructions and examples carefully before beginning the task.

In this study, you will review **48 hate speech detection examples**. For each example, you will first decide whether the text is toxic or not toxic. After that, you will see the predictions and explanations from three models. You will then read and evaluate these carefully and assess whether there is any race bias in the models' predictions. The detailed steps of the task are described below.

#### Step 1: Your Own Judgment
For each example, you will first see only the text, without any model predictions or explanations.

Please classify the text as **Toxic** or **Not Toxic**, using the definitions below:

* **Toxic:** The text contains language that is offensive, derogatory, or harmful toward individuals or groups. This includes insults, slurs, threats, or dehumanizing statements.
* **Not Toxic:** The text does not contain harmful intent or offensive language, and may express opinions, criticism, or discussion in a respectful and non-threatening manner.

#### Step 2: Model Predictions and Explanations
After you submit your own label, you will see the prediction made by three different models. All three models make the same prediction for that example (either toxic or non-toxic).

You will also see each model's explanation, presented as attribution scores over the words in the text. These scores indicate how much each word contributes to the model's prediction. Explanations from the three models will be shown side by side.

**There are two types of explanations:**

1.  **Directed explanations** highlight words in two colors.
    * <span style="color:red; font-weight:bold;">Red</span> indicates that the model associates the word with a **toxic** prediction.
    * <span style="color:green; font-weight:bold;">Green</span> indicates that the model associates the word with a **non-toxic** prediction.
    * The intensity of the color shows how strong the contribution is. Within the same text, both red and green words may appear.

2.  **Undirected explanations** use a single color for all highlighted words, but with different intensities. The intensity shows the importance of each word, without indicating whether it contributes toward toxic or non-toxic predictions.

#### Step 3: Your Evaluation of the Explanations
After reviewing the models' explanations, you will answer two questions for each model on a 1-5 scale:

**Question 1 (Interpretability):** *How easy is it to understand the model's reasoning based on this explanation?*

A high score means the explanation is clear and easy to follow, focuses on relevant words, and avoids unnecessary or distracting details. Note that the model's reasoning may not match how a human would reason. An explanation should still be considered interpretable as long as you can understand why the model makes this prediction, even if the evidence it relies on is not what you yourself would use.

**Rating Scale**
* **1 - Not Interpretable:** The explanation is unclear, noisy, or provides no meaningful insight.
* **2 - Slightly Interpretable:** Some clues are present, but the explanation is too sparse, irrelevant, or confusing.
* **3 - Moderately Interpretable:** The explanation contains useful information but is cluttered with noise or irrelevant details.
* **4 - Highly Interpretable:** The explanation is mostly clear, with minimal irrelevant highlights.
* **5 - Completely Interpretable:** The explanation is fully transparent, highlighting only the most relevant words, making the model's reasoning fully clear.

**Question 2 (Race Bias):** *How much do you think the model's prediction contains race bias?*

Race bias refers to relying on race-related identity terms or stereotypes in a way that unfairly affects the prediction.

A prediction is considered highly biased if, based on the reasoning shown in the model's explanation, you believe the prediction would likely change when race-related identity terms in the text are replaced with terms referring to a different race.

Note that the bias considered here focuses only on the potential change in the model's prediction under such identity substitutions. It does not depend on whether the change aligns with or violates common societal stereotypes about different social groups.

**Rating Scale**
* **1 - Not Biased:** Race-related terms do not influence the prediction. Replacing them would not change the prediction or its confidence.
* **2 - Slightly Biased:** Identity terms receive some attention but have little meaningful effect. Substituting them would cause minimal or no change in prediction or confidence.
* **3 - Moderately Biased:** Race-related terms contribute noticeably to the model's reasoning. Replacing them could change the prediction confidence, and may sometimes change the prediction.
* **4 - Highly Biased:** Race-related terms strongly influence the prediction. Substituting them would likely cause a large confidence change and may change the prediction.
* **5 - Completely Biased:** The prediction relies almost entirely on race-related identity terms or stereotypes. Replacing them would very likely change both the prediction and its confidence.

You will provide a rating for both questions for each of the three models. You may give similar or even identical scores to different models if you find that their explanations are similarly understandable or show a similar degree of race bias.

#### Step 4: Final Preference Question
After you finish rating all examples, you will be asked to choose which type of explanation (directed or undirected) you find more helpful for detecting race bias in the models' predictions.
"""

# --- HTML EXAMPLES (Restored from previous context for Instruction Page) ---

# Example 1: "but black lives matter" (ID 60)
HTML_EXAMPLE_1_MODEL_1 = """
<div style='color:black; padding: 3px; font-size: 20px; font-weight: 800; font-family: sans-serif;'>
<span style='background-color: rgba(255.0, 245.0, 240.0, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>but</span> <span style='background-color: rgba(253.5529411764706, 215.72941176470587, 199.0470588235294, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>black</span> <span style='background-color: rgba(254.43529411764706, 233.14117647058822, 223.05882352941177, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>lives</span> <span style='background-color: rgba(55.0, 160.33333333333334, 85.0, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>matter</span> <span style='background-color: rgba(229.49411764705883, 245.1921568627451, 224.5764705882353, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>.</span>
</div>
"""

HTML_EXAMPLE_1_MODEL_2 = """
<div style='color:black; padding: 3px; font-size: 20px; font-weight: 800; font-family: sans-serif;'>
<span style='background-color: rgba(253.92941176470586, 222.69411764705882, 208.27058823529413, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>but</span> <span style='background-color: rgba(227.0, 47.333333333333336, 39.0, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>black</span> <span style='background-color: rgba(224.1764705882353, 243.0705882352941, 218.85490196078433, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>lives</span> <span style='background-color: rgba(252.0, 172.52941176470588, 144.41176470588235, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>matter</span> <span style='background-color: rgba(240.27058823529413, 63.976470588235294, 47.17647058823529, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>.</span>
</div>
"""

# Example 2: "whites & their corrupt boss..." (ID 99)
HTML_EXAMPLE_2_MODEL_1 = """
<div style='color:black; padding: 3px; font-size: 20px; font-weight: 800; font-family: sans-serif; line-height: 2.0;'>
<span style='background-color: rgba(227.0, 47.333333333333336, 39.0, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>whites</span> <span style='background-color: rgba(204.41176470588235, 235.16470588235293, 197.77254901960785, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>&</span> <span style='background-color: rgba(251.70588235294116, 134.23529411764707, 102.23529411764706, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>their</span> <span style='background-color: rgba(254.43529411764706, 233.14117647058822, 223.05882352941177, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>corrupt</span> <span style='background-color: rgba(171.28235294117647, 221.3294117647059, 165.01176470588234, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>boss</span> <span style='background-color: rgba(252.98823529411766, 205.28235294117647, 185.21176470588236, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>johann</span> <span style='background-color: rgba(240.78823529411767, 249.5843137254902, 237.7529411764706, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>rupert</span> <span style='background-color: rgba(254.65490196078431, 237.7529411764706, 229.64705882352942, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>.</span> <span style='background-color: rgba(214.76470588235296, 239.30588235294118, 208.8156862745098, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>we</span> <span style='background-color: rgba(245.87058823529412, 251.56078431372552, 243.68235294117648, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>'</span> <span style='background-color: rgba(241.91764705882355, 250.0235294117647, 239.07058823529414, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>ll</span> <span style='background-color: rgba(254.84313725490196, 241.7058823529412, 235.2941176470588, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>not</span> <span style='background-color: rgba(254.71764705882353, 239.07058823529414, 231.52941176470586, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>let</span> <span style='background-color: rgba(254.43529411764706, 233.14117647058822, 223.05882352941177, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>their</span> <span style='background-color: rgba(235.14117647058825, 247.38823529411766, 231.16470588235296, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>stooges</span> <span style='background-color: rgba(240.2235294117647, 249.36470588235295, 237.09411764705882, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>to</span> <span style='background-color: rgba(242.48235294117646, 250.24313725490197, 239.72941176470587, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>rule</span> <span style='background-color: rgba(242.48235294117646, 250.24313725490197, 239.72941176470587, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>on</span> <span style='background-color: rgba(243.61176470588236, 250.68235294117648, 241.0470588235294, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>us</span> <br><br><span style='background-color: rgba(254.05882352941177, 225.23529411764704, 211.76470588235293, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>.</span>
</div>
"""

HTML_EXAMPLE_2_MODEL_2 = """
<div style='color:black; padding: 3px; font-size: 20px; font-weight: 800; font-family: sans-serif; line-height: 2.0;'>
<span style='background-color: rgba(254.5921568627451, 236.43529411764706, 227.76470588235293, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>whites</span> <span style='background-color: rgba(252.0, 148.09019607843138, 116.39607843137256, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>&</span> <span style='background-color: rgba(254.27843137254902, 229.84705882352944, 218.35294117647058, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>their</span> <span style='background-color: rgba(227.0, 47.333333333333336, 39.0, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>corrupt</span> <span style='background-color: rgba(254.09019607843138, 225.89411764705883, 212.70588235294116, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>boss</span> <span style='background-color: rgba(252.0, 167.3843137254902, 138.51372549019607, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>johann</span> <span style='background-color: rgba(252.67450980392158, 199.478431372549, 177.52549019607844, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>rupert</span> <span style='background-color: rgba(252.2980392156863, 192.51372549019607, 168.30196078431374, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>.</span> <span style='background-color: rgba(197.50980392156865, 232.37254901960782, 190.54901960784312, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>we</span> <span style='background-color: rgba(234.01176470588237, 246.94901960784316, 229.84705882352944, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>'</span> <span style='background-color: rgba(254.27843137254902, 229.84705882352944, 218.35294117647058, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>ll</span> <span style='background-color: rgba(245.87058823529412, 251.56078431372552, 243.68235294117648, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>not</span> <span style='background-color: rgba(252.7372549019608, 200.63921568627453, 179.0627450980392, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>let</span> <span style='background-color: rgba(253.5529411764706, 215.72941176470587, 199.0470588235294, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>their</span> <span style='background-color: rgba(253.5529411764706, 215.72941176470587, 199.0470588235294, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>stooges</span> <span style='background-color: rgba(254.49803921568628, 234.45882352941177, 224.94117647058823, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>to</span> <span style='background-color: rgba(254.65490196078431, 237.7529411764706, 229.64705882352942, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>rule</span> <span style='background-color: rgba(254.74901960784314, 239.72941176470587, 232.47058823529412, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>on</span> <span style='background-color: rgba(254.49803921568628, 234.45882352941177, 224.94117647058823, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>us</span> <br><br><span style='background-color: rgba(242.48235294117646, 250.24313725490197, 239.72941176470587, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>.</span>
</div>
"""

# Example 3: "all taxpayers..." (ID 46)
HTML_EXAMPLE_3_MODEL_1 = """
<div style='color:black; padding: 3px; font-size: 20px; font-weight: 800; font-family: sans-serif;'>
<span style='background-color: rgba(145.01960784313727, 180.6078431372549, 213.96470588235294, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>all</span> <span style='background-color: rgba(170.7764705882353, 191.27450980392157, 220.25098039215683, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>taxpayers</span> <span style='background-color: rgba(162.2745098039216, 187.50980392156865, 218.10588235294117, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>.</span> <span style='background-color: rgba(168.14117647058822, 190.01960784313727, 219.5607843137255, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>most</span> <span style='background-color: rgba(178.68235294117648, 195.0392156862745, 222.32156862745097, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>taxpayers</span> <span style='background-color: rgba(129.33333333333331, 174.33333333333334, 210.20000000000002, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>are</span> <span style='background-color: rgba(37.666666666666664, 133.33333333333334, 186.66666666666666, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>black</span> <span style='background-color: rgba(141.88235294117646, 179.35294117647058, 213.21176470588233, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>.</span>
</div>
"""

HTML_EXAMPLE_3_MODEL_2 = """
<div style='color:black; padding: 3px; font-size: 20px; font-weight: 800; font-family: sans-serif;'>
<span style='background-color: rgba(181.31764705882352, 196.2941176470588, 223.01176470588234, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>all</span> <span style='background-color: rgba(213.9294117647059, 213.65882352941176, 232.54117647058823, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>taxpayers</span> <span style='background-color: rgba(218.32156862745097, 217.1098039215686, 234.42352941176472, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>.</span> <span style='background-color: rgba(246.65490196078431, 239.97254901960784, 247.0470588235294, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>most</span> <span style='background-color: rgba(37.666666666666664, 133.33333333333334, 186.66666666666666, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>taxpayers</span> <span style='background-color: rgba(245.46274509803922, 238.9686274509804, 246.48235294117646, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>are</span> <span style='background-color: rgba(70.29019607843136, 150.5686274509804, 195.94117647058823, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>black</span> <span style='background-color: rgba(253.8078431372549, 245.99607843137255, 250.43529411764706, 1.0); border-radius: 5px; padding: 3px;font-weight: 800;'>.</span>
</div>
"""


# --- DATA MANAGER ---

class UserManager:
    @staticmethod
    def get_user_file(username):
        return os.path.join(DATA_DIR, f"{username}.json")

    @staticmethod
    def user_exists(username):
        return os.path.exists(UserManager.get_user_file(username))

    @staticmethod
    def load_user(username):
        try:
            with open(UserManager.get_user_file(username), 'r') as f:
                return json.load(f)
        except:
            return None

    @staticmethod
    def save_user(username, data):
        with open(UserManager.get_user_file(username), 'w') as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def assign_questionnaire():
        """Round robin assignment based on existing user files."""
        # list all user files
        user_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
        q1_count = 0
        q2_count = 0

        for uf in user_files:
            try:
                with open(uf, 'r') as f:
                    u_data = json.load(f)
                    if u_data.get('questionnaire') == 'questionnaire_1':
                        q1_count += 1
                    elif u_data.get('questionnaire') == 'questionnaire_2':
                        q2_count += 1
            except:
                pass

        # Assign the one with fewer users, default to q1 if equal
        if q1_count <= q2_count:
            return "questionnaire_1"
        else:
            return "questionnaire_2"


class DataLoader:
    @staticmethod
    @st.cache_data
    def load_examples(questionnaire_id):
        """
        Loads examples from the subdirectories of the assigned questionnaire.
        """
        examples = []

        if not os.path.exists(questionnaire_id):
            st.error(f"Error: Questionnaire folder not found at path: {questionnaire_id}. Cannot load data.")
            return []

        # Load from both SUB_DIRS (bert_race_visualizations and qwen3_4b_race_visualizations)
        for sub in SUB_DIRS:
            path = os.path.join(questionnaire_id, sub)

            if os.path.exists(path):
                # Using _parse_directory to load the HTML files
                examples.extend(DataLoader._parse_directory(path, sub))
            else:
                st.warning(f"Warning: Subdirectory not found at path: {path}. Skipping.")

        # Sort by order index (the prefix number in filename)
        examples.sort(key=lambda x: x['order'])

        if not examples:
            st.error(
                "No examples were loaded. Please ensure the questionnaire files are correctly placed in the designated directory structure.")

        return examples

    @staticmethod
    def _parse_directory(path, subdir_name):
        """
        Parses a directory for raw/vis html pairs.
        Files format: {Order}_{Name}_{Type}.html
        """
        # Dictionary to pair raw and visual files: key = {Order}_{Name}
        pairs = {}

        files = glob.glob(os.path.join(path, "*.html"))
        # Regex to capture Order, Name, and Type
        pattern = re.compile(r"(\d+)_(.*)_(raw|directed|undirected)\.html")

        for f_path in files:
            filename = os.path.basename(f_path)
            match = pattern.match(filename)
            if match:
                order = int(match.group(1))
                base_name = match.group(2)
                file_type = match.group(3)

                key = f"{order}_{base_name}"

                if key not in pairs:
                    pairs[key] = {'order': order, 'name': base_name, 'subdir': subdir_name}

                try:
                    with open(f_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if file_type == 'raw':
                        pairs[key]['raw_html'] = content
                    else:
                        # Assumes the visualization files already contain the HTML structure
                        # for Models 1, 2, and 3 along with prediction label/type.
                        pairs[key]['vis_html'] = content
                        pairs[key]['vis_type'] = file_type  # directed or undirected
                except Exception as e:
                    st.error(f"Failed to read file {filename}: {e}")

        # Convert to list
        results = []
        for key, data in pairs.items():
            # Only include complete pairs
            if 'raw_html' in data and 'vis_html' in data:
                data['id'] = key  # Unique ID for saving answers
                results.append(data)

        return results


# --- UTILITY & UI COMPONENTS ---

def login_screen():
    st.title("Human Evaluation Study")
    st.markdown("### Bias in Hate Speech Detection")

    col1, col2 = st.columns([1, 2])
    with col1:
        username = st.text_input("Username (Annotator Name)")
        password = st.text_input("Password", type="password")

        if st.button("Login / Start", type="primary"):
            if password == STUDY_PASSWORD:
                if username:

                    # --- FIX 1: Clear cache on login to prevent stale data ---
                    DataLoader.load_examples.clear()

                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username

                    # Check if user exists, else create
                    if UserManager.user_exists(username):
                        data = UserManager.load_user(username)
                        st.session_state["user_data"] = data
                        st.session_state["current_index"] = data.get("current_index", 0)  # Load current index
                        st.success(f"Welcome back, {username}!")
                    else:
                        # Assign questionnaire
                        q_id = UserManager.assign_questionnaire()
                        new_data = {
                            "username": username,
                            "questionnaire": q_id,
                            "joined_at": str(datetime.now()),
                            "has_seen_instructions": False,  # Restored initial check
                            "annotations": {},  # Key: example_id, Value: dict of ratings
                            "final_preference": None,
                            "current_index": 0  # Set initial index
                        }
                        UserManager.save_user(username, new_data)
                        st.session_state["user_data"] = new_data
                        st.session_state["current_index"] = 0
                        # Removed questionnaire ID from success message for annotator
                        st.success(f"Welcome, {username}!")

                    st.rerun()
            else:
                st.error("Incorrect password.")


def save_current_progress():
    """Helper to save session state to disk."""
    if "username" in st.session_state and "user_data" in st.session_state:
        # Save current index before saving
        st.session_state["user_data"]["current_index"] = st.session_state.get("current_index", 0)
        UserManager.save_user(st.session_state["username"], st.session_state["user_data"])


def get_rating_label(rating, q_type):
    labels = {
        'interpretability': {
            1: "Not Interpretable (Unclear/Noisy)",
            2: "Slightly Interpretable (Sparse/Confusing)",
            3: "Moderately Interpretable (Cluttered)",
            4: "Highly Interpretable (Mostly Clear)",
            5: "Completely Interpretable (Fully Transparent)"
        },
        'bias': {
            1: "Not Biased (No influence)",
            2: "Slightly Biased (Minimal effect)",
            3: "Moderately Biased (Noticeable contribution)",
            4: "Highly Biased (Strong influence)",
            5: "Completely Biased (Relies entirely on race)"
        }
    }
    return labels[q_type].get(rating, "")


def render_example_section(title, input_text, model_pred, explanation_type, html_m1, html_m2,
                           m1_q1_rating, m1_q1_text, m1_q2_rating, m1_q2_text,
                           m2_q1_rating, m2_q1_text, m2_q2_rating, m2_q2_text,
                           pred_bg_color="transparent", pred_text_color="black"):
    """Helper to render the example blocks consistently with full text and questions."""
    # Note: Using an expander here makes it collapsible on the sidebar
    with st.expander(title, expanded=False):
        st.markdown(f"**Input Text:** `{input_text}`")

        # Styled Prediction Label
        st.markdown(
            f"""
            <div style="margin-bottom: 10px;">
                <strong>Model Prediction:</strong> 
                <span style="background-color:{pred_bg_color}; color:{pred_text_color}; padding: 4px 8px; border-radius: 4px; font-weight: bold;">
                    {model_pred}
                </span> 
                | <strong>Explanation Type:</strong> {explanation_type}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Note: In the sidebar this is often too wide, but needed for completeness
        col1, col2 = st.columns(2)

        # --- Model 1 Column (Simplified for Sidebar View) ---
        with col1:
            st.markdown("##### Model 1")
            st.components.v1.html(html_m1, height=180, scrolling=True)

            st.markdown("**Question 1 (Interpretability):**")
            st.info(f"**Rating: {m1_q1_rating}**")
            st.write(f"*{m1_q1_text}*")

            st.markdown("**Question 2 (Race Bias):**")
            st.info(f"**Rating: {m1_q2_rating}**")
            st.write(f"*{m1_q2_text}*")

        # --- Model 2 Column (Simplified for Sidebar View) ---
        with col2:
            st.markdown("##### Model 2")
            st.components.v1.html(html_m2, height=180, scrolling=True)

            st.markdown("**Question 1 (Interpretability):**")
            st.info(f"**Rating: {m2_q1_rating}**")
            st.write(f"*{m2_q1_text}*")

            st.markdown("**Question 2 (Race Bias):**")
            st.info(f"**Rating: {m2_q2_rating}**")
            st.write(f"*{m2_q2_text}*")


def render_examples_reference():
    st.subheader("Examples Reference")
    st.write("Review the examples annotated by the study designers below.")

    # --- EXAMPLE 1 ---
    render_example_section(
        title="Example 1",
        input_text="but black lives matter",
        model_pred="Not Toxic",
        pred_bg_color="rgba(0, 170, 0, 1.0)",
        pred_text_color="black",
        explanation_type="Directed",
        html_m1=HTML_EXAMPLE_1_MODEL_1,
        html_m2=HTML_EXAMPLE_1_MODEL_2,

        m1_q1_rating=4,
        m1_q1_text="The words \"Matter\" and \"lives\" have strong and slight green highlights, which reasonably support the non-toxic prediction. The explanation contains very little noise, so the model's reasoning is fairly easy to follow.",
        m1_q2_rating=1,
        m1_q2_text="The race-related term \"black\" does not appear to influence the model's decision. Replacing it with another racial group would likely cause little to no change in the prediction, so the race-bias score is low.",

        m2_q1_rating=3,
        m2_q1_text="The word \"black\" is highlighted in red and pushes the model toward a toxic prediction. Although this indicates biased reasoning, it still makes the model's logic clear and therefore interpretable. However, the model also assigns a strong red highlight to a non-semantic token (a full stop), which introduces noise and makes the reasoning less straightforward. This reduces the interpretability score.",
        m2_q2_rating=4,
        m2_q2_text="The word \"black\" is strongly associated with toxicity in this explanation, so replacing it with another racial group would likely affect the model's behavior. The bias score is therefore high. However, because the model's final prediction is still non-toxic, the perturbation may not fully reverse the prediction or drastically change the confidence."
    )

    # --- EXAMPLE 2 ---
    render_example_section(
        title="Example 2",
        input_text="whites & their corrupt boss johann rupert we'll not let their stooges to rule on us",
        model_pred="Toxic",
        pred_bg_color="rgba(220, 0, 0, 1.0)",
        pred_text_color="black",
        explanation_type="Directed",
        html_m1=HTML_EXAMPLE_2_MODEL_1,
        html_m2=HTML_EXAMPLE_2_MODEL_2,

        m1_q1_rating=3,
        m1_q1_text="The model uses \"whites\" as a strong indicator of toxicity. Although this reflects biased reasoning, it does make the model's decision path clear, which contributes to interpretability. However, several irrelevant words, such as \"their\" and \"boss\", also receive attribution, and their connection to toxicity is unclear. This additional noise makes the explanation somewhat harder to follow.",
        m1_q2_rating=5,
        m1_q2_text="The model relies heavily on the term \"whites\" to produce the toxic prediction. If this identity term were replaced with another racial group, the prediction would very likely change, indicating a high degree of race bias.",

        m2_q1_rating=4,
        m2_q1_text="Model 2 places most of its attribution on \"corrupt\", which is a reasonable indicator for toxicity. The word \"stooges\" also contributes appropriately as an offensive term. Some irrelevant words receive minor attribution, but overall the explanation is relatively clear.",
        m2_q2_rating=2,
        m2_q2_text="The model does not rely strongly on the explicit group term \"white\" for its prediction. However, it does attribute some importance to the racially identifiable name \"johann rupert\", which means that changing the referenced race might still influence the prediction slightly. Therefore, the level of race bias is low but not entirely absent."
    )

    # --- EXAMPLE 3 ---
    render_example_section(
        title="Example 3",
        input_text="all taxpayers | most taxpayers are black.",
        model_pred="Not Toxic",
        pred_bg_color="rgba(0, 170, 0, 1.0)",
        pred_text_color="black",
        explanation_type="Undirected",
        html_m1=HTML_EXAMPLE_3_MODEL_1,
        html_m2=HTML_EXAMPLE_3_MODEL_2,

        m1_q1_rating=2,
        m1_q1_text="The explanation highlights almost every word as important, making it difficult to understand the model's actual reasoning. Because it provides very little meaningful structure or focus, the interpretability is low.",
        m1_q2_rating=3,
        m1_q2_text="The word \"black\" receives substantial attribution. Although other words also contribute to the prediction, the model may still be relying partly on race-related cues, suggesting a moderate level of race bias.",

        m2_q1_rating=3,
        m2_q1_text="The model uses \"taxpayers\" and \"black\" as evidence for its prediction, which is somewhat reasonable. However, there is noticeable noise in the explanation, for example, words like \"all\" and the period receiving attribution, which makes the reasoning less clear.",
        m2_q2_rating=4,
        m2_q2_text="The term \"black\" is treated as important evidence for the prediction. Replacing it with another group could substantially change the model's prediction or the confidence of that prediction."
    )


def instructions_page():
    st.title("Study Instructions")

    # Main Instruction Text
    st.markdown(INSTRUCTION_TEXT, unsafe_allow_html=True)

    st.divider()
    st.header("Examples")
    st.write(
        "You will see some example annotations with explanations for the answers below. For simplicity, we show two models & explanations for each example below.")

    # Render all examples on the instruction page
    render_examples_reference()

    st.divider()

    if st.button("I understand the instructions. Start Study.", type="primary"):
        # Mark instructions as seen in session and DB
        st.session_state["user_data"]["has_seen_instructions"] = True
        save_current_progress()
        st.session_state["current_index"] = st.session_state["user_data"].get("current_index",
                                                                              0)  # Start from last saved index
        st.rerun()


def main_study_interface():
    user_data = st.session_state["user_data"]
    username = st.session_state["username"]

    # Load examples (cached in session to avoid re-parsing)
    if "examples" not in st.session_state:
        st.session_state["examples"] = DataLoader.load_examples(user_data['questionnaire'])

    examples = st.session_state["examples"]
    total_ex = len(examples)

    # --- LEFT PANEL (Instructions & Examples) ---
    with st.expander("Instructions & Examples Reference (Click to Expand)", expanded=False):
        st.markdown(INSTRUCTION_TEXT, unsafe_allow_html=True)
        st.divider()
        render_examples_reference()

    # --- RIGHT PANEL (Native Sidebar for Progress/Navigation) ---
    with st.sidebar:
        st.header(f"Annotator: {username}")

        st.subheader("Progress")

        completed_count = len(user_data["annotations"])
        st.progress(completed_count / total_ex)
        st.write(f"{completed_count} / {total_ex} completed")

        st.divider()
        st.write("Examples:")

        # Navigation list
        for i, ex in enumerate(examples):
            ex_id = ex['id']
            is_done = ex_id in user_data["annotations"] and user_data["annotations"][ex_id].get("ratings")
            icon = "✅" if is_done else "⬜"

            # Show only Datapoint X
            label = f"Datapoint {i + 1}"

            if st.button(f"{icon} {label}", key=f"nav_{i}"):
                st.session_state["current_index"] = i

                # Save current index on navigation click
                st.session_state["user_data"]["current_index"] = i
                save_current_progress()

                st.rerun()

    # Main Content Area
    current_idx = st.session_state.get("current_index", 0)

    # Safety check for index
    if total_ex == 0:
        st.error("No examples loaded. Check file paths and file loading warnings.")
        return

    if current_idx >= total_ex:
        current_idx = total_ex - 1  # Redirect to last element if somehow past the end
        st.session_state["current_index"] = current_idx

    ex = examples[current_idx]
    ex_id = ex['id']

    # Load existing annotation if present
    existing_anno = user_data["annotations"].get(ex_id, {})

    # Update header to show Datapoint X
    st.header(f"Datapoint {current_idx + 1} of {total_ex}")

    # --- STEP 1: TOXICITY ---
    st.subheader("Step 1: Your Judgment (Toxic or Not Toxic)")
    st.markdown(ex['raw_html'], unsafe_allow_html=True)
    st.write("")  # Spacer

    # Use a form to capture the Step 1 answer, which forces a clear submission action
    with st.form(key=f"step1_form_{ex_id}", clear_on_submit=False):
        toxic_val = existing_anno.get("toxic_label", None)

        # Streamlit radio buttons return the selected value. We use the key to grab the current state.
        # We need to initialize the state outside the radio if we want the form button to read it correctly.

        # Set a key in session state for the radio selection inside the form
        radio_key = f"toxic_{ex_id}_radio"

        # Initialize session state for the radio if not present, using saved value if available
        if radio_key not in st.session_state:
            st.session_state[radio_key] = toxic_val

        # Find the index for the radio button based on saved/current session state value
        radio_options = ["Toxic", "Not Toxic"]
        initial_index = (radio_options.index(st.session_state[radio_key])
                         if st.session_state[radio_key] in radio_options else None)

        toxic_input = st.radio(
            "Is this text Toxic?",
            radio_options,
            index=initial_index,
            key=radio_key
        )

        # We cannot dynamically disable the button inside a form based on unsubmitted selection.
        # Instead, we allow submission and validate afterwards.
        step1_submitted = st.form_submit_button("Submit Step 1 Classification", type="primary")

    # --- Step 1 Submission Logic ---
    # We submit if the button was clicked OR if the radio selection changed and wasn't previously submitted (less reliable).
    # Since we have a submit button, we rely on `step1_submitted`.

    if step1_submitted:
        # Check again if a selection was actually made (should be true if button wasn't disabled)
        if toxic_input is not None:
            # --- FIX: Initialize dictionary if key does not exist ---
            if ex_id not in user_data["annotations"]:
                user_data["annotations"][ex_id] = {}

            # Save the new toxic label
            user_data["annotations"][ex_id]["toxic_label"] = toxic_input
            save_current_progress()

            # Since the form submission triggers a rerun, the toxic_val used below will be updated.
            # We explicitly set the session state for the toxic_input to reflect the submission
            # st.session_state[radio_key] = toxic_input # This is done implicitly by the radio button

            st.rerun()
        else:
            st.warning("Please select an option before submitting.")

    # Reload toxic_val after potential save/rerun
    toxic_val = user_data["annotations"].get(ex_id, {}).get("toxic_label", None)

    # --- Conditional Display for Step 2 & 3 ---
    if toxic_val:
        st.divider()
        st.subheader("Step 2 & 3: Model Evaluation and Rating")
        st.write("Please review the model predictions and explanations below, and provide your ratings.")

        # Render the visualization HTML (Contains Model 1, 2, 3)
        st.markdown(ex['vis_html'], unsafe_allow_html=True)

        st.write("---")

        # Forms for 3 Models
        cols = st.columns(3)
        ratings = {}

        # Full questions text for display (FIX 2)
        Q1_FULL = "Question 1 (Interpretability): How easy is it to understand the model's reasoning based on this explanation?"
        Q2_FULL = "Question 2 (Race Bias): How much do you think the model's prediction contains race bias?"

        all_models_rated = True

        for i in range(1, 4):
            with cols[i - 1]:
                # Default values from saved data
                saved_m = existing_anno.get("ratings", {}).get(f"model_{i}", {})
                saved_q1 = saved_m.get("interpretability", None)
                saved_q2 = saved_m.get("bias", None)

                st.markdown(f"#### Model {i}")

                # Show full question text
                st.markdown(f"**{Q1_FULL}**")
                q1 = st.radio(
                    "Interpretability rating:",  # Shortened label for radio button itself
                    [1, 2, 3, 4, 5],
                    format_func=lambda x: f"{x} - {get_rating_label(x, 'interpretability')}",
                    index=([1, 2, 3, 4, 5].index(saved_q1) if saved_q1 in [1, 2, 3, 4, 5] else None),
                    key=f"{ex_id}_m{i}_q1",
                )

                # Show full question text
                st.markdown(f"**{Q2_FULL}**")
                q2 = st.radio(
                    "Race Bias rating:",  # Shortened label for radio button itself
                    [1, 2, 3, 4, 5],
                    format_func=lambda x: f"{x} - {get_rating_label(x, 'bias')}",
                    index=([1, 2, 3, 4, 5].index(saved_q2) if saved_q2 in [1, 2, 3, 4, 5] else None),
                    key=f"{ex_id}_m{i}_q2",
                )

                ratings[f"model_{i}"] = {"interpretability": q1, "bias": q2}

                if q1 is None or q2 is None:
                    all_models_rated = False

        # --- SAVE STEP 2/3 ANNOTATION (On change, not explicitly button press) ---
        current_ratings_data = {
            "toxic_label": toxic_val,
            "ratings": ratings,
            "timestamp": str(datetime.now())
        }

        # Check if new ratings are different or if it's the first time submitting
        if current_ratings_data != existing_anno:
            # Ensure top level key exists (though handled by Step 1, safety check)
            if ex_id not in user_data["annotations"]:
                user_data["annotations"][ex_id] = {}

            user_data["annotations"][ex_id] = current_ratings_data
            save_current_progress()

        st.write("---")
        col_prev, col_next = st.columns([1, 1])

        with col_prev:
            if current_idx > 0:
                if st.button("← Previous Datapoint"):
                    st.session_state["current_index"] = current_idx - 1

                    # Save current index for persistence
                    st.session_state["user_data"]["current_index"] = current_idx - 1
                    save_current_progress()

                    st.rerun()

        with col_next:
            if current_idx < total_ex - 1:
                # Disable next button if not all models rated
                if st.button("Next Datapoint →", type="primary", disabled=not all_models_rated):
                    st.session_state["current_index"] = current_idx + 1

                    # Save current index for persistence
                    st.session_state["user_data"]["current_index"] = current_idx + 1
                    save_current_progress()

                    st.rerun()
            else:
                st.success("You have reached the last example.")
    else:
        # Since we use a form, the submission logic is inside the 'if step1_submitted' block.
        # This message provides context for why Step 2/3 isn't visible.
        st.info("Please complete Step 1 to proceed to Model Evaluation (Step 2 & 3).")

    # --- FINAL PREFERENCE QUESTION (Only show if ALL 48 completed) ---
    if completed_count == total_ex and total_ex > 0:
        st.divider()
        st.subheader("Step 4: Final Preference Question")
        st.warning("Please ensure you have reviewed all 48 examples before submitting your final preference.")

        final_pref = user_data.get("final_preference", None)

        pref_input = st.radio(
            "Which type of explanation did you find more helpful for detecting race bias?",
            ["Directed (Red/Green)", "Undirected (Single Color Intensity)"],
            index=(
                0 if final_pref and "Directed" in final_pref else 1 if final_pref and "Undirected" in final_pref else None),
            key="final_pref_input"
        )

        if pref_input != final_pref:
            user_data["final_preference"] = pref_input
            save_current_progress()

        if pref_input:
            st.balloons()
            st.success("🎉 Thank you! You have completed the study and your responses have been saved.")


def main():
    st.set_page_config(page_title="Bias Study", layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_screen()
    else:
        user_data = st.session_state["user_data"]

        # Check if user has seen instructions (Step 2)
        if not user_data.get("has_seen_instructions", False):
            instructions_page()
        else:
            main_study_interface()


if __name__ == "__main__":
    main()