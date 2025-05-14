#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, json, re
import subprocess
from urllib.parse import unquote


with open("./wiki_tools/config/setting.json") as f:
    config = json.load(f)

with open(config["structure"]) as f:
    structure = json.load(f)


def link_text(entity, link, hash=None):
    if hash is None:
        hash = ""
    else:
        hash = "#"+hash
    
    if config["link_style"] == "global":
        # with global link style
        return "["+entity+"]("+config["url"]+link+hash+")"
    elif config["link_style"] == "local":
        # with local link style
        return "[["+entity+"|"+link+hash+"]]"
    elif config["link_style"] == "wiki":
        # with wiki link style
        return "["+entity+"]("+link+hash+")"
    else:
        # default: with wiki link style
        return "["+entity+"]("+link+hash+")"

def get_latest_update():
    # 過去のcommit logと照らし合わせて最終更新日ごとに並べる
    result = subprocess.run(
        """cd ./.wiki ; git ls-files . | xargs -I@ -P0 bash -c 'echo "$(git log -1 --format="%aI" -- @)" @' | sort -r""", 
        shell=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #print("STDOUT:", result.stdout)
    #print("STDERR:", result.stderr)
    return [ _.split()[1] for _ in result.stdout.strip().split("\n") ]

def generate_index_of_page(filename):
    #print(filename)
    pagename = filename.split("/")[-1]
    pagename = pagename.split(".")[0]

    sol = '<!-- start_index_of_page -->\n'
    eol = '<!-- end_index_of_page -->\n'

    data = []
    with open(config["dir"]+"/"+filename) as f:
        data = f.readlines()

    try:
        index_sol = data.index(sol)
        index_eol = data.index(eol)
    except:
        return

    min_depth = 10000
    for line in data[index_eol:]:
        if re.match("^#+ ", line) is not None:
            depth = len(re.match("^#+ ", line).group(0)) - 1
            if depth <= min_depth:
                min_depth = depth
                
    list_of_h = []
    for line in data[index_eol:]:
        if re.match("^#+ ", line) is not None:
            depth = len(re.match("^#+ ", line).group(0)) - 1
            section_name = ' '.join(line.split(" ")[1:]).strip()
            section_hash = '-'.join(line.split(" ")[1:]).replace("/","").replace("(", "-").replace(")", "-").strip("-").strip()

            list_of_h.append( "  " * (depth - min_depth) + "* " + link_text(+section_name, pagename, hash=section_hash)+"\n" )

    with open(config["dir"]+"/"+filename, "w") as f:
        f.writelines(data[:index_sol+1])
        f.writelines(list_of_h)
        f.writelines(data[index_eol:])


def generate_index_of_child_pages(filename, list_of_pages):
    pagename = filename.split("/")[-1]
    pagename = pagename.split(".")[0]
    page_depth = len(pagename.split("_"))

    sol = '<!-- start_index_of_child_pages -->\n'
    eol = '<!-- end_index_of_child_pages -->\n'

    data = []
    with open(config["dir"]+"/"+filename) as f:
        data = f.readlines()

    try:
        index_sol = data.index(sol)
        index_eol = data.index(eol)
    except Exception as e:
        #print(e)
        return
        

    new_data = []
    new_data.extend(data[:index_sol+1])
    for child in sorted(list_of_pages):
        if child.startswith(pagename) and child != pagename:
            child_page_depth = len(child.split("_"))
            child_page_name = "_".join(child.split("_")[page_depth:])
            new_data.extend('  '*(child_page_depth-page_depth-1) + "* "+link_text(child_page_name,child)+"\n")
    new_data.extend(data[index_eol:])

    if data != new_data:
        with open(config["dir"]+"/"+filename, "w") as f:
            f.writelines(new_data)

def generate_list_of_illegal_pages(filename, list_of_illegal_pages):
    pagename = filename.split("/")[-1]
    pagename = pagename.split(".")[0]
    page_depth = len(pagename.split("_"))

    sol = '<!-- start_list_of_illegal_named_pages -->\n'
    eol = '<!-- end_list_of_illegal_named_pages -->\n'

    data = []
    with open(config["dir"]+"/"+filename) as f:
        data = f.readlines()

    try:
        index_sol = data.index(sol)
        index_eol = data.index(eol)
    except Exception as e:
        #print(e)
        return
    
    new_data = []
    new_data.extend(data[:index_sol+1])
    new_data.extend([ "* [["+_+"]]\n" for _ in list_of_illegal_pages ])
    new_data.extend(data[index_eol:])

    if data != new_data:
        with open(config["dir"]+"/"+filename, "w") as f:
            f.writelines(new_data)


def generate_breadcrumbs(filename, list_of_pages):
    #print(filename)

    pagename = filename.split("/")[-1]
    pagename = pagename.split(".")[0]

    sol = '<!-- start_breadcrumbs -->\n'
    eol = '<!-- end_breadcrumbs -->\n'

    data = []
    with open(config["dir"]+"/"+filename) as f:
        data = f.readlines()

    try:
        index_sol = data.index(sol)
        index_eol = data.index(eol)
    except Exception as e:
        data.insert(0, sol)
        data.insert(1, eol)
        data.insert(2, "")
        
        index_sol = data.index(sol)
        index_eol = data.index(eol)
        

    new_data = []
    new_data.extend(data[:index_sol+1])
    bar = ""
    if pagename != "Home":
        bar += link_text("Home", "Home")+" > "
        for pos, name in enumerate(pagename.split("_")):
            if "_".join(pagename.split("_")[:pos+1]) in list_of_pages:
                bar += link_text(name, "_".join(pagename.split("_")[:pos+1]))
            else:
                bar += name
            if pos < len(pagename.split("_")) - 1 :
                bar += " > "

    # sidebar等は追加しない
    if pagename[0] != "_":
        bar += "\n"
        new_data.append(bar)

    new_data.extend(data[index_eol:])

    if data != new_data:
        with open(config["dir"]+"/"+filename, "w") as f:
            f.writelines(new_data)


def add_auto_link(filename, list_of_pages):
#    print(list_of_pages)
    print("###add_auto_link:", filename)
    entites = {}
    for pagename in sorted(list_of_pages, key=lambda x:len(x)):
        try:
            entity = pagename.split("_")[-1]
            if len(entity) <= 1: continue
            if entity in entites.keys(): continue
            entites[entity] = pagename
        except:
            pass

    with open(config["dir"]+"/"+filename) as f:
        data = "".join(f.readlines())
    new_data = data

    # 正規表現: マッチして置換
    # 古いパターンのautolink tag
    # この書き方だと箇条書きの先頭がautolinkになった場合にうまく表記されない
    pattern = r"<!--start_autolink-->\[(.*?)\]\(.*?\)<!--end_autolink-->"
    replacement = r"\1"  # キャプチャグループ1 (括弧内のテキスト) に置換
    new_data = re.sub(pattern, replacement, new_data)
    #print(new_data)
    
    # 正規表現: マッチして置換
    # 古いパターンのautolink tag
    # この書き方だとobsidianでlink認識されない
    pattern = r"\[(.*?)\]\(.*?\)<!--add_autolink-->"
    replacement = r"\1"  # キャプチャグループ1 (括弧内のテキスト) に置換
    new_data = re.sub(pattern, replacement, new_data)
    #print(new_data)
    
    # 古いパターンのautolink tag
    # この書き方だと箇条書きの先頭がautolinkになった場合にうまく表記されない
    pattern = r"\[\[(.*?)\|(.*?)\]\]<!--add_autolink-->"
    replacement = r"\1"  # キャプチャグループ1 (括弧内のテキスト) に置換
    #print(replacement)
    #print(new_data)
    new_data = re.sub(pattern, replacement, new_data)
    #print(new_data)

    # ページ名に一致するならリンクする
    for entity, link in sorted(entites.items(), key=lambda x:len(x[0]), reverse=True):
        #print(entity, link)
        new_data = replace_text_outside_markdown(new_data, entity, link_text(entity, link)+"<!--add_autolink-->")
    if data != new_data:
        with open(config["dir"]+"/"+filename, "w") as f:
            f.writelines(new_data)
    
    return

def replace_text_outside_markdown(text, target, replacement):
    # Markdownの記法に該当する部分（リンク、コード、太字、見出しなど）をパターン化
    markdown_patterns = [
        r'<!--.+?-->',        # コメント<!-- -->
        r'\*\*[^\n\r]+?\*\*',        # **太字**
        r'\*[^\n\r]+?\*',            # *斜体*
        r'`[^\n\r]+?`',              # インラインコード
        r'\[.*?\]\(.*?\)',     # リンク記法 [テキスト](URL)
        r'\[\[.*?\]\]',     # リンク記法 [テキスト](URL)
        r'!\[.*?\]\(.*?\)',    # 画像リンク記法 ![alt](URL)
        r'\[\[(.*?)\|(.*?)\]\]',    # リンク記法 [[alt|alt]]
        r'^```[\s\S]*?```',    # コードブロック
        r'^#+ [^\n\r]+?$',             # 見出し記法（# 見出し）
        r'\|.*?\|',             # table
    ]
    
    # Markdown部分をプレースホルダで置き換え
    placeholders = []       # プレースホルダのリスト
    def placeholder_replacer(match):
        placeholder = '<PLACEHOLDER-'+str(len(placeholders))+'>'  # 特殊な文字（適宜変更可能）
        placeholders.append(match.group(0))
        return placeholder

    # Markdown記法に該当する部分をプレースホルダに変換
    #print("original", text)
    for pattern in markdown_patterns:
        text = re.sub(pattern, placeholder_replacer, text, flags=re.MULTILINE)

#    print("placehold", text)
    # 指定文字列を置き換え
    text = re.sub(fr'(?<!\w){re.escape(target)}(?!\w)', replacement, text)
    #print("replaced", text)
    # プレースホルダを元のMarkdown部分に戻す
    for i, placeholder_text in enumerate(reversed(placeholders)):
        placeholder = '<PLACEHOLDER-'+str(len(placeholders) - i - 1)+'>'  # 特殊な文字（適宜変更可能）
        text = text.replace(placeholder, placeholder_text, 1)
    #print("restored", text)
    return text

def find_link(data):
    list_of_linked_pages = []

    sol = '<!-- start_list_of_illegal_named_pages -->\n'
    eol = '<!-- end_list_of_illegal_named_pages -->\n'
    try:
        index_sol = data.index(sol)
        index_eol = data.index(eol)

        data = data[:index_sol]+data[index_eol:]
    except Exception as e:
        pass

    sol = '<!-- start_list_of_recent_updated_pages -->\n'
    eol = '<!-- end_list_of_recent_updated_pages -->\n'
    try:
        index_sol = data.index(sol)
        index_eol = data.index(eol)

        data = data[:index_sol]+data[index_eol:]
    except Exception as e:
        pass

    # URLリンクの正規表現
    pattern1 = fr'\[([^]]+)\]\(({config["url"]}[^)]+)\)'
    # LOCALリンクの正規表現
    pattern2 = r'\[\[([^]]+)\]\]'
    # Wikiリンクの正規表現
    pattern3 = r'\[([^]]+)\]\(([^)]+)\)'

    for l in data:
        # global linkの場合はURL以降のファイル名に相当する部分を抜き出す
        matches = re.finditer(pattern1, l)
        for match in matches:
            text1 = match.group(1)
            text2 = match.group(2)
            text2 = text2.split("#")[0]
            text2 = text2.split("/")[-1]
            text2 = unquote(text2)

            list_of_linked_pages.append(text2)

        # local linkの場合は|以降のファイル名に相当する部分を抜き出す
        matches = re.finditer(pattern2, l)
        for match in matches:
            text1 = match.group(1)

            list_of_linked_pages.append(text1)

        # wiki linkの場合は()のファイル名に相当する部分を抜き出す
        matches = re.finditer(pattern3, l)
        for match in matches:
            text1 = match.group(1)
            list_of_linked_pages.append(text1)

    return list_of_linked_pages

def preprocess():
    list_of_pages = []
    list_of_illegal_pages = []

    # リンク先ページの一覧を取得
    list_of_linked_pages = []
    for filename in os.listdir(config["dir"]):
        if filename[0] == "." : continue
        # .git以外に.gitignoreも排除するために頭文字が.の場合は対象にしないよう変更
        if ".md" not in filename: continue
        # markdonw以外のファイルも対象外にする

#        print("Preprocess:"+filename)
        with open(config["dir"]+"/"+filename) as f:
            list_of_linked_pages.extend(find_link(f.readlines()))

    for filename in os.listdir["dir"](config["dir"]):
        if filename[0] == "." : continue
        # .git以外に.gitignoreも排除するために頭文字が.の場合は対象にしないよう変更
        if ".md" not in filename: continue
        # markdonw以外のファイルも対象外にする

        pagename = filename.split("/")[-1]
        pagename = pagename.split(".")[0]
        page_depth = pagename.split("_")

        list_of_pages.append(pagename)

        next_structure = structure
        is_illegal_page = False
        for depth, name in enumerate(page_depth):
#            print(depth, name)
            next_structure = next_structure.get(name, "illegal")
            if next_structure == "illegal":
                is_illegal_page = True
                list_of_illegal_pages.append(pagename)
#                print(pagename, "is bad page name!")
                add_notification_message(filename, "このページの名前は不適切です．")
                break
            if len(next_structure.keys()) == 0: 
                break
        
        if not is_illegal_page: 
            if pagename[0] != "_" and not pagename in list_of_linked_pages: 
#                print(pagename, "is not linked!")
                add_notification_message(filename, "このページはどこからもリンクされていません．")
                list_of_illegal_pages.append(pagename)
            else:
                delete_notification_message(filename)
            continue

    list_of_pages = list(set(list_of_pages))
    list_of_illegal_pages = list(set(list_of_illegal_pages))
    return list_of_pages, list_of_illegal_pages

def add_notification_message(filename, message):

    eol = '<!-- end_notification_message -->\n'
    with open(config["dir"]+"/"+filename) as f:
        data = f.readlines()

    new_data = data
    try:
        index_eol = data.index(eol)
        new_data = data[index_eol+1:]
    except Exception as e:
        pass

    insert_message = f"""> [!CAUTION]
> {message}
<!-- end_notification_message -->
"""

    new_data.insert(0, insert_message)

    if data != new_data:
        with open(config["dir"]+"/"+filename, "w") as f:
            f.writelines(new_data)
        
def delete_notification_message(filename):

    eol = '<!-- end_notification_message -->\n'
    with open(config["dir"]+"/"+filename) as f:
        data = f.readlines()

    new_data = data
    try:
        index_eol = data.index(eol)
        new_data = data[index_eol+1:]
    except Exception as e:
        pass
    
    if data != new_data:
        with open(config["dir"]+"/"+filename, "w") as f:
            f.writelines(new_data)

def generate_sidebar(list_of_pages):
    # generage Sidebar.md        
    with open(config["sidebar"]) as f:
        sidebar = json.load(f)

    #print(sidebar)
    with open(config["dir"]+"/_Sidebar.md", "w") as f:
        f.write("# メニュー\n")

        for index, max_depth in sidebar["sidebar_sort"].items():
            if not index in list_of_pages:
                #print(index, "is not exist page.")
                f.write("* "+index+"\n")

            for pagename in sorted(list_of_pages):
                depth = pagename.split("_")
                if len(depth) > max_depth: continue
                if pagename[0] == "_": continue
                if depth[0] == index:
                    f.write("  " * (len(depth) - 1) + "* "+link_text(depth[-1],pagename)+"\n")                    
#                    print(depth, depth[-1], pagename)

        f.write("***\n")
        f.write("# 最近更新されたページ\n")
        f.write("<!-- start_list_of_recent_updated_pages -->\n")
        i = 0
        for filename in get_latest_update():
            if filename[0] == "_": continue
            if filename[0] == ".": continue
            pagename=filename.split(".")[0]
            f.write("* "+link_text(pagename, pagename)+"\n")
            i += 1
            if i >= config["num_recent"]: break
        f.write("<!-- end_list_of_recent_updated_pages -->\n")


def main():
    list_of_pages, list_of_illegal_pages = preprocess()

    for filename in os.listdir(config["dir"]):
        # 処理対象外ファイルの設定
        # .git以外に.gitignoreも排除するために頭文字が.の場合は対象にしないよう変更
        if filename[0] == "." : continue
        # markdonw以外のファイルも対象外にする
        if ".md" not in filename: continue
        
        pagename = filename.split("/")[-1]
        pagename = pagename.split(".")[0]

        if config["generate_sidebar"]:
            # sidebar
            generate_sidebar(list_of_pages)
        if config["add_breadcrumbs"]:
            # パンくずリスト
            generate_breadcrumbs(filename, list_of_pages)
        if config["add_auto_link"]:
            # 自動リンク
            add_auto_link(filename, list_of_pages)
        if config["check_structure"]:
            # 違反ページ一覧を生成
            generate_list_of_illegal_pages(filename, list_of_illegal_pages)
        if config["add_index_of_pages"]:
            # ページの目次を生成
            generate_index_of_page(filename)
            # 子ページの一覧を生成
            generate_index_of_child_pages(filename, list_of_pages)
    return

if __name__=="__main__":
    main()