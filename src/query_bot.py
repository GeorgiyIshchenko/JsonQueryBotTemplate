import json
from dataclasses import dataclass, field

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CallbackQueryHandler


@dataclass
class QueryNode(object):
    message_title: str = "Empty message"
    callback_id: int = None
    button_name: str = None
    message_body: str = None
    image_path: str = None
    video_path: str = None
    previous: int = None
    url_buttons: list = field(default_factory=list)
    children: list = field(default_factory=list)


@dataclass
class UrlButton(object):
    name: str
    url: str


class QueryBot(object):
    current_node_id: int = 0
    callbacks: dict = dict()
    file_path: str
    app: Application | None = None

    ROOT_ID = 1

    @staticmethod
    def get_current_node_id():
        QueryBot.current_node_id += 1
        return QueryBot.current_node_id

    @staticmethod
    async def base_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query

        if query:
            await query.answer()
            message = query.message
            node: QueryNode = QueryBot.callbacks[int(query.data)]
        else:
            message = update.message
            node: QueryNode = QueryBot.callbacks[QueryBot.ROOT_ID]

        keyboard: list[list[InlineKeyboardButton]] = list()

        for child_id in node.children:
            child = QueryBot.callbacks[child_id]
            keyboard.append([InlineKeyboardButton(text=child.button_name, callback_data=str(child_id))])

        for url_button in node.url_buttons:
            keyboard.append([InlineKeyboardButton(text=url_button.name, url=url_button.url)])

        if node.previous:
            keyboard.append([InlineKeyboardButton(text="Назад", callback_data=str(node.previous))])

        reply_markup = InlineKeyboardMarkup(keyboard) if len(keyboard) else None

        if node.video_path:
            await message.reply_video(caption=node.message_title, video=node.video_path, supports_streaming=True,
                                      reply_markup=reply_markup)

        elif node.image_path:
            await message.reply_photo(caption=node.message_title, photo=node.image_path,
                                      reply_markup=reply_markup)

        else:
            await message.reply_text(text=node.message_title, reply_markup=reply_markup)

    @staticmethod
    def unpack_recursive(node: QueryNode, child_data: dict) -> None:
        child: QueryNode = QueryNode()
        node_id: int = QueryBot.get_current_node_id()
        child.callback_id = node_id
        child.message_title = child_data.get("message_title", None)
        child.button_name = child_data.get("button_name", None)
        child.message_body = child_data.get("message_body", None)
        child.image_path = child_data.get("image_path", None)
        child.video_path = child_data.get("video_path", None)
        child.previous = node.callback_id

        for url_button_data in child_data.get("url_buttons", list()):
            button: UrlButton = UrlButton(name=url_button_data.get("name"), url=url_button_data.get("url"))
            child.url_buttons.append(button)

        QueryBot.callbacks[node_id] = child
        node.children.append(node_id)

        if child_data.get("children", None) is not None:
            child_children = child_data['children']
            for i in range(len(child_children)):
                QueryBot.unpack_recursive(child, child_children[i])

    @staticmethod
    def init():

        root_json = json.load(open(QueryBot.file_path, 'r', encoding='utf-8'))
        root: QueryNode = QueryNode(message_title=root_json['message_title'])
        root_children = root_json['children']

        root_id = QueryBot.get_current_node_id()
        root.callback_id = root_id
        QueryBot.callbacks[root_id] = root

        for i in range(len(root_children)):
            QueryBot.unpack_recursive(root, root_children[i])

        for i in QueryBot.callbacks.items():
            print(i)

        QueryBot.app.add_handler(CallbackQueryHandler(QueryBot.base_handler, ''))
