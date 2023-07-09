from flask import Flask, render_template, request
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chat_models import ChatOpenAI
import openai

app = Flask(__name__)

API_KEY = "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"

def get_completion_from_messages(character, theme, background, age, language):
    try:        
        chat = ChatOpenAI(openai_api_key=API_KEY, max_tokens=100)

        response_schemas = [
            ResponseSchema(name="title",
                           description='<the title of each chapter>'           
            ),
            ResponseSchema(name="content",
                           description='<the content of each chapter>'
            ),
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()
    
        sysTemplate = """You are a children story teller who gives neat story.\
            The words and phrases must follow strict rule that makes the story appropriate for children. \
            The difficulty of fairy tales should be appropriate for a {input_age}-year-old child. \
            Use the character, theme and background delimited by ####. \
            character:####{input_character}#### \
            theme:####{input_theme}#### \
            background:####{input_background}#### \
            {format_instructions}
        """
        system_message_prompt = SystemMessagePromptTemplate.from_template(sysTemplate)
        humanTemplate = """
            Give me the very first chapter. In 4 sentences.
        """
        human_message_prompt = HumanMessagePromptTemplate.from_template(humanTemplate)

        chat_prompt = ChatPromptTemplate(
            messages= [system_message_prompt, human_message_prompt],
            input_variables= ["input_age", "input_character", "input_theme", "input_background"],
            partial_variables={"format_instructions": format_instructions}
        )
        _input = chat_prompt.format_prompt(input_age=age, input_character=character, input_theme=theme, input_background=background)
        output = chat(_input.to_messages())
        return output_parser.parse(output.content)

    except Exception as e:
        print(e)

def get_translated_messages(chapterObj, lang):
    try:
        chat = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo", openai_api_key=API_KEY)

        title = chapterObj['title']
        content = chapterObj['content']

        response_schemas = [
        ResponseSchema(name="title", description="<translated title>"),
        ResponseSchema(name="content", description="<translated content>"),
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()

        trans_prompt_template = """
        Please, translate the texts to target_language delimited with ####. \
        texts must be translated by children friendly tone.
        title:####{input_title}#### \
        content:####{input_content}#### \
        target_language:####{input_lang}#### \
        {format_instructions}
        """

        trans_prompt = ChatPromptTemplate.from_template(template=trans_prompt_template)
        messages = trans_prompt.format_messages(input_title=title, input_content=content, input_lang=lang, format_instructions=format_instructions)

        trans_res = chat(messages)

        return output_parser.parse(trans_res.content)
    
    except Exception as e:
        print(e)

def get_picture(chapter):
        chat = ChatOpenAI(temperature=1, model="gpt-3.5-turbo", openai_api_key=API_KEY)

        response_schemas = [
        ResponseSchema(name="summary", description="<summarized text>"),
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()

        keywords_prompt_template= """
        Please summarize the text in one short sentence delimited by ####. \
        text:####{chapter}#### \
        {format_instructions}
        """
        keywords_prompt = ChatPromptTemplate.from_template(
            template=keywords_prompt_template
        )

        messages = keywords_prompt.format_messages(chapter=chapter['content'], format_instructions=format_instructions)

        keywords_res = chat(messages)

        keywords_parsed = output_parser.parse(keywords_res.content)

        print(keywords_parsed)

        image_prompt = f"{keywords_parsed}, painterly, children's book, colorful, medium strokes"

        image = openai.Image.create(
        api_key=API_KEY,
        prompt=image_prompt,
        n=1,
        size="1024x1024"
        )

        print(image["data"])

        return image["data"]



@app.route("/", methods=["POST", "GET"])
def hello_world():
    return render_template('base.html')

@app.route("/create", methods=["POST", "GET"])
def create():
    if request.method == 'POST':
        character = request.form['character']
        theme = request.form['theme']
        background = request.form['background']
        age = request.form['age']
        language = request.form['language']

        res = get_completion_from_messages(character, theme, background, age, language)
        print('res', res)

        trans_res = get_translated_messages(res, language)
        print(trans_res)

        image_url = get_picture(res)

        return render_template('story.html', res=res, image_url=image_url[0]["url"])
    else:
        return render_template('story.html')