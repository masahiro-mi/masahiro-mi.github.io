#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, json, re
import subprocess
from urllib.parse import unquote


class WikiToolGenerator:
    def __init__(self, config_path):
        with open(config_path) as f:
            self.config = json.load(f)
        with open(self.config["structure"]) as f:
            self.structure = json.load(f)

    def link_text(self, entity, link, hash=None, link_style=None):
        hash = f"#{hash}" if hash else ""
        link_styles = {
            "global": f"[{entity}]({self.config['url']}{link}{hash})",
            "local": f"[[{entity}|{link}{hash}]]",
            "wiki": f"[{entity}]({link}{hash})"
        }
        link_style = link_style or self.config["link_style"]
        return link_styles.get(link_style, link_styles["wiki"])

    def get_latest_update(self):
        result = subprocess.run(
            """cd ./.wiki ; git ls-files . | xargs -I@ -P0 bash -c 'echo \"$(git log -1 --format=\"%aI\" -- @)\" @' | sort -r""",
            shell=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return [line.split()[1] for line in result.stdout.strip().split("\n")]

    def generate_index_of_page(self, filename):
        pagename = filename.split("/")[-1].split(".")[0]
        sol, eol = '<!-- start_index_of_page -->\n', '<!-- end_index_of_page -->\n'

        with open(f"{self.config['dir']}/{filename}") as f:
            data = f.readlines()

        try:
            index_sol, index_eol = data.index(sol), data.index(eol)
        except ValueError:
            return

        min_depth = min((len(re.match("^#+ ", line).group(0)) - 1 for line in data[index_eol:] if re.match("^#+ ", line)), default=10000)
        list_of_h = [
            "  " * (len(re.match("^#+ ", line).group(0)) - 1 - min_depth) + "* " + self.link_text(' '.join(line.split(" ")[1:]).strip(), pagename, hash='-'.join(line.split(" ")[1:]).replace("/", "").replace("(", "-").replace(")", "-").strip("-")) + "\n"
            for line in data[index_eol:] if re.match("^#+ ", line)
        ]

        with open(f"{self.config['dir']}/{filename}", "w") as f:
            f.writelines(data[:index_sol + 1] + list_of_h + data[index_eol:])

    def generate_index_of_child_pages(self, filename, list_of_pages):
        pagename = filename.split("/")[-1].split(".")[0]
        page_depth = len(pagename.split("_"))

        sol, eol = '<!-- start_index_of_child_pages -->\n', '<!-- end_index_of_child_pages -->\n'

        with open(f"{self.config['dir']}/{filename}") as f:
            data = f.readlines()

        try:
            index_sol, index_eol = data.index(sol), data.index(eol)
        except ValueError:
            return

        new_data = data[:index_sol + 1]
        for child in sorted(list_of_pages):
            if child.startswith(pagename) and child != pagename:
                child_page_depth = len(child.split("_"))
                child_page_name = "_".join(child.split("_")[page_depth:])
                new_data.append('  ' * (child_page_depth - page_depth - 1) + "* " + self.link_text(child_page_name, child) + "\n")
        new_data.extend(data[index_eol:])

        if data != new_data:
            with open(f"{self.config['dir']}/{filename}", "w") as f:
                f.writelines(new_data)

    def generate_list_of_illegal_pages(self, filename, list_of_illegal_pages):
        pagename = filename.split("/")[-1].split(".")[0]

        sol, eol = '<!-- start_list_of_illegal_named_pages -->\n', '<!-- end_list_of_illegal_named_pages -->\n'

        with open(f"{self.config['dir']}/{filename}") as f:
            data = f.readlines()

        try:
            index_sol, index_eol = data.index(sol), data.index(eol)
        except ValueError:
            return

        new_data = data[:index_sol + 1]
        new_data.extend([f"* [[{page}]]\n" for page in list_of_illegal_pages])
        new_data.extend(data[index_eol:])

        if data != new_data:
            with open(f"{self.config['dir']}/{filename}", "w") as f:
                f.writelines(new_data)

    def generate_breadcrumbs(self, filename, list_of_pages):
        pagename = filename.split("/")[-1].split(".")[0]

        sol, eol = '<!-- start_breadcrumbs -->\n', '<!-- end_breadcrumbs -->\n'

        with open(f"{self.config['dir']}/{filename}") as f:
            data = f.readlines()

        try:
            index_sol, index_eol = data.index(sol), data.index(eol)
        except ValueError:
            data.insert(0, sol)
            data.insert(1, eol)
            data.insert(2, "")
            index_sol, index_eol = data.index(sol), data.index(eol)

        new_data = data[:index_sol + 1]
        bar = ""
        if pagename != "Home":
            bar += self.link_text("Index", "index") + " → "
            for pos, name in enumerate(pagename.split("_")):
                if "_".join(pagename.split("_")[:pos + 1]) in list_of_pages:
                    bar += self.link_text(name, "_".join(pagename.split("_")[:pos + 1]))
                else:
                    bar += name
                if pos < len(pagename.split("_")) - 1:
                    bar += " → "

        if pagename[0] != "_":
            bar += "\n"
            new_data.append(bar)

        new_data.extend(data[index_eol:])

        if data != new_data:
            with open(f"{self.config['dir']}/{filename}", "w") as f:
                f.writelines(new_data)

    
    def generate_footer(self, filename):
        pagename = filename.split("/")[-1].split(".")[0]

        sol, eol = '<!-- start_footer -->\n', '<!-- end_footer -->\n'

        with open(f"{self.config['dir']}/{filename}") as f:
            data = f.readlines()

        try:
            index_sol, index_eol = data.index(sol), data.index(eol)
        except ValueError:
            data.insert(-1, sol)
            data.insert(-1, eol)
            data.insert(-1, "")
            index_sol, index_eol = data.index(sol), data.index(eol)

        new_data = data[:index_sol + 1]
        footer = ""
        footer += "-----\n"
        footer += "[:link:Site](https://individuality.jp/wiki/"+filename+") / [:pen:Edit](https://github.com/masahiro-mi/masahiro-mi.github.io/wiki/"+filename+"/_edit)"
        new_data.extend(data[index_eol:])

        if data != new_data:
            with open(f"{self.config['dir']}/{filename}", "w") as f:
                f.writelines(new_data)

    def preprocess(self):
        list_of_pages = []
        list_of_illegal_pages = []

        list_of_linked_pages = []
        for filename in os.listdir(self.config["dir"]):
            if filename.startswith(".") or not filename.endswith(".md"):
                continue

            with open(f"{self.config['dir']}/{filename}") as f:
                list_of_linked_pages.extend(self.find_link(f.readlines()))

        for filename in os.listdir(self.config["dir"]):
            if filename.startswith(".") or not filename.endswith(".md"):
                continue

            pagename = filename.split("/")[-1].split(".")[0]
            page_depth = pagename.split("_")

            list_of_pages.append(pagename)

            next_structure = self.structure
            is_illegal_page = False
            for depth, name in enumerate(page_depth):
                next_structure = next_structure.get(name, "illegal")
                if next_structure == "illegal":
                    is_illegal_page = True
                    list_of_illegal_pages.append(pagename)
                    self.add_notification_message(filename, "このページの名前は不適切です．")
                    break
                if len(next_structure.keys()) == 0:
                    break

            if not is_illegal_page:
                if pagename[0] != "_" and pagename not in list_of_linked_pages:
                    self.add_notification_message(filename, "このページはどこからもリンクされていません．")
                    list_of_illegal_pages.append(pagename)
                else:
                    self.delete_notification_message(filename)
                continue

        list_of_pages = list(set(list_of_pages))
        list_of_illegal_pages = list(set(list_of_illegal_pages))
        return list_of_pages, list_of_illegal_pages

    def generate_sidebar(self, list_of_pages):
        with open(self.config["sidebar"]) as f:
            sidebar = json.load(f)

        with open(f"{self.config['dir']}/_Sidebar.md", "w") as f:
            f.write("# メニュー\n")

            for index, max_depth in sidebar["sidebar_sort"].items():
                if index not in list_of_pages:
                    f.write(f"* {index}\n")

                for pagename in sorted(list_of_pages):
                    depth = pagename.split("_")
                    if len(depth) > max_depth or pagename[0] == "_":
                        continue
                    if depth[0] == index:
                        f.write("  " * (len(depth) - 1) + f"* {self.link_text(depth[-1], pagename, hash=None, link_style='wiki')}\n")

            f.write("***\n")
            f.write("# 最近更新されたページ\n")
            f.write("<!-- start_list_of_recent_updated_pages -->\n")
            for i, filename in enumerate(self.get_latest_update()):
                if filename[0] == "_" or filename[0] == ".":
                    continue
                pagename = filename.split(".")[0]
                f.write(f"* {self.link_text(pagename, pagename, hash=None, link_style='wiki')}\n")
                if i >= self.config["num_recent"] - 1:
                    break
            f.write("<!-- end_list_of_recent_updated_pages -->\n")

    def add_notification_message(self, filename, message):
        eol = '<!-- end_notification_message -->\n'
        with open(f"{self.config['dir']}/{filename}") as f:
            data = f.readlines()

        new_data = data
        try:
            index_eol = data.index(eol)
            new_data = data[index_eol + 1:]
        except ValueError:
            pass

        insert_message = f"""> [!CAUTION]
> {message}
<!-- end_notification_message -->
"""

        new_data.insert(0, insert_message)

        if data != new_data:
            with open(f"{self.config['dir']}/{filename}", "w") as f:
                f.writelines(new_data)

    def delete_notification_message(self, filename):
        eol = '<!-- end_notification_message -->\n'
        with open(f"{self.config['dir']}/{filename}") as f:
            data = f.readlines()

        new_data = data
        try:
            index_eol = data.index(eol)
            new_data = data[index_eol + 1:]
        except ValueError:
            pass

        if data != new_data:
            with open(f"{self.config['dir']}/{filename}", "w") as f:
                f.writelines(new_data)

    def find_link(self, data):
        list_of_linked_pages = []

        sol, eol = '<!-- start_list_of_illegal_named_pages -->\n', '<!-- end_list_of_illegal_named_pages -->\n'
        try:
            index_sol, index_eol = data.index(sol), data.index(eol)
            data = data[:index_sol] + data[index_eol:]
        except ValueError:
            pass

        sol, eol = '<!-- start_list_of_recent_updated_pages -->\n', '<!-- end_list_of_recent_updated_pages -->\n'
        try:
            index_sol, index_eol = data.index(sol), data.index(eol)
            data = data[:index_sol] + data[index_eol:]
        except ValueError:
            pass

        pattern1 = fr'\[([^]]+)\]\(({self.config["url"]}[^)]+)\)'
        pattern2 = r'\[\[([^]]+)\]\]'
        pattern3 = r'\[([^]]+)\]\(([^)]+)\)'

        for line in data:
            matches = re.finditer(pattern1, line)
            for match in matches:
                text2 = match.group(2).split("#")[0].split("/")[-1]
                list_of_linked_pages.append(unquote(text2))

            matches = re.finditer(pattern2, line)
            for match in matches:
                list_of_linked_pages.append(match.group(1))

            matches = re.finditer(pattern3, line)
            for match in matches:
                list_of_linked_pages.append(match.group(1))

        return list_of_linked_pages

    def add_auto_link(self, filename, list_of_pages):
        """Automatically adds links to other pages in the content."""
        print("###add_auto_link:", filename)
        entities = {}
        for pagename in sorted(list_of_pages, key=lambda x: len(x)):
            try:
                entity = pagename.split("_")[-1]
                if len(entity) <= 1:
                    continue
                if entity in entities.keys():
                    continue
                entities[entity] = pagename
            except Exception:
                pass

        with open(f"{self.config['dir']}/{filename}") as f:
            data = "".join(f.readlines())
        new_data = data

        # Replace old autolink patterns
        patterns = [
            (r"<!--start_autolink-->\[(.*?)\]\(.*?\)<!--end_autolink-->", r"\1"),
            (r"\[(.*?)\]\(.*?\)<!--add_autolink-->", r"\1"),
            (r"\[\[(.*?)\|(.*?)\]\]<!--add_autolink-->", r"\1")
        ]

        for pattern, replacement in patterns:
            new_data = re.sub(pattern, replacement, new_data)

        # Add new autolinks for matching page names
        for entity, link in sorted(entities.items(), key=lambda x: len(x[0]), reverse=True):
            new_data = self.replace_text_outside_markdown(new_data, entity, self.link_text(entity, link) + "<!--add_autolink-->")

        if data != new_data:
            with open(f"{self.config['dir']}/{filename}", "w") as f:
                f.writelines(new_data)

        return

    def replace_text_outside_markdown(self, text, target, replacement):
        """Replaces occurrences of target with replacement outside Markdown code blocks."""
        markdown_patterns = [
            r'```(?:.*?\n)?[\s\S]*?```',    # コードブロック（複数行対応）
            r'`[^\n\r]+?`',              # インラインコード
            r'\[.*?\]\(.*?\)',     # リンク記法 [テキスト](URL)
            r'\[\[.*?\]\]',     # リンク記法 [テキスト](URL)
            r'!\[.*?\]\(.*?\)',    # 画像リンク記法 ![alt](URL)
            r'\[\[(.*?)\|(.*?)\]\]',    # リンク記法 [[alt|alt]]
            r'^#+ [^\n\r]+?$',             # 見出し記法（# 見出し）
            r'\|.*?\|',             # テーブル
            r'<!--.+?-->',        # コメント<!-- -->
            r'\*\*[^\n\r]+?\*\*',        # **太字**
            r'\*[^\n\r]+?\*',            # *斜体*
        ]

        placeholders = []

        def placeholder_replacer(match):
            placeholder = f'<PLACEHOLDER-{len(placeholders)}>'
            placeholders.append(match.group(0))
            return placeholder

        for pattern in markdown_patterns:
            text = re.sub(pattern, placeholder_replacer, text, flags=re.MULTILINE)

        text = re.sub(fr'(?<!\w){re.escape(target)}(?!\w)', replacement, text)

        for i, placeholder_text in enumerate(reversed(placeholders)):
            placeholder = f'<PLACEHOLDER-{len(placeholders) - i - 1}>'
            text = text.replace(placeholder, placeholder_text, 1)

        return text


def main():
    generator = WikiToolGenerator("./wiki_tools/config/setting.json")
    list_of_pages, list_of_illegal_pages = generator.preprocess()

    for filename in os.listdir(generator.config["dir"]):
        if filename.startswith(".") or not filename.endswith(".md"):
            continue

        if generator.config["generate_sidebar"]:
            generator.generate_sidebar(list_of_pages)
        if generator.config["add_breadcrumbs"]:
            generator.generate_breadcrumbs(filename, list_of_pages)
        if generator.config["add_auto_link"]:
            generator.add_auto_link(filename, list_of_pages)
        if generator.config["add_footer"]:
            generator.generate_footer(filename)
        if generator.config["check_structure"]:
            generator.generate_list_of_illegal_pages(filename, list_of_illegal_pages)
        if generator.config["add_index_of_pages"]:
            generator.generate_index_of_page(filename)
            generator.generate_index_of_child_pages(filename, list_of_pages)


if __name__ == "__main__":

    main()
