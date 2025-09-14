import enum
import bookmark
from reportlab.lib import colors
import json
import re


class Messages(bookmark.Document):
    def __init__(self):
        super().__init__()

    # def drawEmojiString(self, x, y, text):
    #     cursor_x = x
    #     parts = emoji_pattern.split(text)
    #     emojis = emoji_pattern.findall(text)
    #     font = self.font
    #
    #     for i, part in enumerate(parts):
    #         # Draw normal text
    #         if part:
    #             self.setfont(font)
    #             self.canvas.drawString(cursor_x, y, part)
    #             cursor_x += self.canvas.stringWidth(part, font, font.size)
    #
    #         # Draw emoji (if any after this part)
    #         if i < len(emojis):
    #             emoji = emojis[i]
    #             self.setfont("Emoji")
    #             self.canvas.drawString(cursor_x, y, emoji)
    #             cursor_x += self.canvas.stringWidth(emoji, "Emoji", 12)
    #     self.setfont(font)

    def get_messages(self):
        msg_data = []
        for i in range(3):
            with open(f"./message_{i+1}.json", "r") as f:
                data = json.load(f)["messages"]
                msg_data += data
        msg_data.reverse()

        messages = []
        for msg in msg_data:
            if "content" in msg:
                # messages.append(msg["sender_name"].split(" ")[0].upper()+": "+msg["content"].encode("latin-1").decode("utf-8"))
                # messages.append(msg["content"].encode("latin-1").decode("utf-8"))
                messages.append({"sender": msg["sender_name"].split(" ")[0].lower(), "content": msg["content"].encode("latin-1").decode("utf-8")})
        return messages

    def split(self):
        messages = self.get_messages()[0::]
        text = " ".join([msg["content"] for msg in messages]).replace("\n", " ")
        leading = int(self.font.size * 1.2)
        pages = self.justifytext(text, leading=leading)

        m1 = 0
        m2 = 0
        for page in pages:
            for line in page:
                for data in line:
                    x, y, word = data
                    x -= 1.4
                    if word not in messages[m1]["content"]:
                        m1 += 1
                    sender = messages[m1]["sender"]
                    w = self.canvas.stringWidth(word, self.font, self.font.size)+20
                    h = leading
                    hpad = (h-self.font.size)
                    y -= hpad*2
                    color = (colors.black, colors.white) if sender == "dylan" else (colors.pink, colors.black)
                    self.canvas.setFillColor(color[0])
                    self.canvas.rect(x, y, w, h, fill=1, stroke=0)
            for line in page:
                for data in line:
                    x, y, word = data
                    if word not in messages[m2]["content"]:
                        m2 += 1
                    sender = messages[m2]["sender"]
                    color = (colors.black, colors.white) if sender == "dylan" else (colors.pink, colors.black)
                    self.canvas.setFillColor(color[1])
                    self.canvas.drawString(*data)
            self.newpage()

        

        # messages = self.get_messages()
        # text = []
        # for msg in messages:
        #     text.append(msg["content"])
        # text = " ".join(text).replace("\n", " ")
        # paradata = self.paragraphdata(text)
        #
        # i = 0
        # last_sender = ""
        # for m, msg in enumerate(messages):
        #     sender = msg["sender"]
        #     content = msg["content"]
        #     words = content.split(" ")
        #     # print(words)
        #
        #     for data in paradata[i:i+len(words)]:
        #         pword = data[2]
        #         if pword == ";newpage()":
        #             self.newpage()
        #         else:
        #             x = data[0]
        #             y = data[1]
        #             w = self.canvas.stringWidth(pword, self.font, self.font.size)
        #             h = self.font.size
        #             color = (colors.black, colors.white) if sender == "dylan" else (colors.white, colors.black)
        #             self.canvas.setFillColor(color[0])
        #             self.canvas.rect(x, y, w, h, fill=1, stroke=0)
        #             self.canvas.setFillColor(color[1])
        #             self.setfont(self.font)
        #             self.drawEmojiString(x, y, pword)
        #         i += 1


            # for word in words:
            #     pword = paradata[i][2]
            #     if pword == ";newpage()":
            #         self.newpage()
            #         i += 1
            #     pword = paradata[i][2]
            #     print(pword == word)
            #     x = paradata[i][0]
            #     y = paradata[i][1]
            #     w = self.canvas.stringWidth(word, self.font, self.font.size)
            #     h = self.font.size
            #     color = (colors.black, colors.white) if sender == "dylan" else (colors.white, colors.black)
            #     self.canvas.setFillColor(color[0])
            #     self.canvas.rect(x, y, w, h, fill=1, stroke=0)
            #     self.canvas.setFillColor(color[1])
            #     self.canvas.drawString(x, y, word)
            #
            #     i += 1
            

        # self.paragraph(text)


bookmark.loop(path=Messages().path)
