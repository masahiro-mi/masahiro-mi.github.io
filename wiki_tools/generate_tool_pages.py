#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, json, re
import subprocess
from urllib.parse import unquote


dir = "./.wiki"
base_url = "https://individuality.jp/wiki/"

with open("./wiki_tools/config/structure.json") as f:
    structure = json.load(f)

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
    with open(dir+"/"+filename) as f:
        data = f.readlines()

    try:
        index_sol = data.index(sol)
        index_eol = data.index(eol)
#        print(index_sol, index_eol)
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
#        print(line, re.match("^#+ ", line).group(0))
        if re.match("^#+ ", line) is not None:
            depth = len(re.match("^#+ ", line).group(0)) - 1
            section_name = ' '.join(line.split(" ")[1:]).strip()
            section_hash = '-'.join(line.split(" ")[1:]).replace("/","").strip()
            #print(depth, section_hash)
                                    
            list_of_h.append( "  " * (depth - min_depth) + "* " + "["+section_name+"]("+base_url+pagename+"#"+section_hash+")\n" )

    #print(list_of_h)
    with open(dir+"/"+filename, "w") as f:
        f.writelines(data[:index_sol+1])
        f.writelines(list_of_h)
        f.writelines(data[index_eol:])


def generate_index_of_child_pages(filename, list_of_pages):
    #print(filename)
    pagename = filename.split("/")[-1]
    pagename = pagename.split(".")[0]
    page_depth = len(pagename.split("_"))

    sol = '<!-- start_index_of_child_pages -->\n'
    eol = '<!-- end_index_of_child_pages -->\n'

    data = []
    with open(dir+"/"+filename) as f:
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
            new_data.extend('  '*(child_page_depth-page_depth-1) + "* "+"["+child_page_name+"]("+base_url+child+")\n")
    new_data.extend(data[index_eol:])

    if data != new_data:
        with open(dir+"/"+filename, "w") as f:
            f.writelines(new_data)



def generate_index_of_all_pages(filename, list_of_pages):
    pagename = filename.split("/")[-1]
    pagename = pagename.split(".")[0]

    sol = '<!-- start_index_of_all_pages -->\n'
    eol = '<!-- end_index_of_all_pages -->\n'

    data = []
    with open(dir+"/"+filename) as f:
        data = f.readlines()

    try:
        index_sol = data.index(sol)
        index_eol = data.index(eol)
    except Exception as e:
        #print(e)
        return
        

    new_data = []
    new_data.extend(data[:index_sol+1])
    previous_depth = 0
    for child in sorted(list_of_pages):
#        if child.startswith(pagename) and child != pagename:
            child_page_depth = len(child.split("_"))
            child_page_name = "_".join(child.split("_")[-1])
            if previous_depth <= child_page_depth:
                new_data.extend('  '*(child_page_depth-1) + "* "+"["+child_page_name+"]("+base_url+child+")\n")
            else:
                for i in range(0, child_page_depth-1):
                    #print('  '*(i-1) + "* "+child.split("_")[i])
                    new_data.extend('  '*(i-1) + "* "+child.split("_")[i]+'\n')
                new_data.extend('  '*(child_page_depth-1) + "* "+"["+child_page_name+"]("+base_url+child+")\n")

    new_data.extend(data[index_eol:])

    if data != new_data:
        with open(dir+"/"+filename, "w") as f:
            f.writelines(new_data)


def generate_list_of_illegal_pages(filename, list_of_illegal_pages):
    #print(filename)
    pagename = filename.split("/")[-1]
    pagename = pagename.split(".")[0]
    page_depth = len(pagename.split("_"))

    sol = '<!-- start_list_of_illegal_named_pages -->\n'
    eol = '<!-- end_list_of_illegal_named_pages -->\n'

    data = []
    with open(dir+"/"+filename) as f:
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
        with open(dir+"/"+filename, "w") as f:
            f.writelines(new_data)

def add_auto_link(filename, list_of_pages):
#    print(list_of_pages)
    print("add_auto_link:", filename)
    entites = {}
    for pagename in sorted(list_of_pages, key=lambda x:len(x)):
        try:
            entity = pagename.split("_")[-1]
            if len(entity) <= 1: continue
            if entity in entites.keys(): continue
            entites[entity] = pagename
        except:
            pass
    # リンク可能entiry
#    print(entites.items())

    with open(dir+"/"+filename) as f:
        data = "".join(f.readlines())
    new_data = data

    # 正規表現: マッチして置換
    pattern = r"<!--start_autolink-->\[(.*?)\]\(.*?\)<!--end_autolink-->"
    replacement = r"\1"  # キャプチャグループ1 (括弧内のテキスト) に置換
    new_data = re.sub(pattern, replacement, new_data)

    # ページ名に一致するならリンクする
    for entity, link in sorted(entites.items(), key=lambda x:len(x[0]), reverse=True):
        #print(entity, link)
        new_data = replace_text_outside_markdown(new_data, entity, "<!--start_autolink-->["+entity+"]("+base_url+link+")<!--end_autolink-->")
    
    if data != new_data:
        with open(dir+"/"+filename, "w") as f:
            f.writelines(new_data)

    #with open(dir+"/"+filename, "w") as f:
    #    f.write(data)
    print(data)

    return

def replace_text_outside_markdown(text, target, replacement):
    # Markdownの記法に該当する部分（リンク、コード、太字、見出しなど）をパターン化
    markdown_patterns = [
        r'<!--.+?-->',        # コメント<!-- -->
        r'\*\*[^\n\r]+?\*\*',        # **太字**
        r'\*[^\n\r]+?\*',            # *斜体*
        r'`[^\n\r]+?`',              # インラインコード
        r'\[.*?\]\(.*?\)',     # リンク記法 [テキスト](URL)
        r'!\[.*?\]\(.*?\)',    # 画像リンク記法 ![alt](URL)
        r'^```[\s\S]*?```',    # コードブロック
        r'^#+ [^\n\r]+?$',             # 見出し記法（# 見出し）
    ]
    
    # Markdown部分をプレースホルダで置き換え
    placeholders = []       # プレースホルダのリスト
    def placeholder_replacer(match):
        placeholder = '<PLACEHOLDER-'+str(len(placeholders))+'>'  # 特殊な文字（適宜変更可能）
        placeholders.append(match.group(0))
        #print(placeholder, placeholders)
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
    for i, placeholder_text in enumerate(placeholders):
        placeholder = '<PLACEHOLDER-'+str(i)+'>'  # 特殊な文字（適宜変更可能）
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

    pattern1 = rf'\[([^]]+)\]\(({base_url}[^)]+)\)'
    pattern2 = r'\[\[([^]]+)\]\]'
    for l in data:
        matches = re.finditer(pattern1, l)

        for match in matches:
            text1 = match.group(1)
            text2 = match.group(2)
#                    print(f"text1: {text1}, text2: {text2}")
            text2 = text2.split("#")[0]
            text2 = text2.split("/")[-1]
            text2 = unquote(text2)

            list_of_linked_pages.append(text2)

        matches = re.finditer(pattern2, l)

        for match in matches:
            text1 = match.group(1)

            list_of_linked_pages.append(text1)

    return list_of_linked_pages

def preprocess():
    list_of_pages = []
    list_of_illegal_pages = []

    # リンク先ページの一覧を取得
    list_of_linked_pages = []
    for filename in os.listdir(dir):
        if filename == ".git" : continue
#        print("Preprocess:"+filename)
        with open(dir+"/"+filename) as f:
            list_of_linked_pages.extend(find_link(f.readlines()))

    for filename in os.listdir(dir):
        if filename == ".git" : continue
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
    with open(dir+"/"+filename) as f:
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
        with open(dir+"/"+filename, "w") as f:
            f.writelines(new_data)
        
def delete_notification_message(filename):

    eol = '<!-- end_notification_message -->\n'
    with open(dir+"/"+filename) as f:
        data = f.readlines()

    new_data = data
    try:
        index_eol = data.index(eol)
        new_data = data[index_eol+1:]
    except Exception as e:
        pass
    
    if data != new_data:
        with open(dir+"/"+filename, "w") as f:
            f.writelines(new_data)

def generate_sidebar(list_of_pages):
    # generage Sidebar.md        
    with open("./wiki_tools/config/sidebar.json") as f:
        sidebar = json.load(f)
    #print(sidebar)
    with open(dir+"/_Sidebar.md", "w") as f:
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
                    f.write("  " * (len(depth) - 1) + "* [["+depth[-1]+"|"+pagename+"]]\n")
#                    print(depth, depth[-1], pagename)

        f.write("***\n")
        f.write("# 最近更新されたページ\n")
        f.write("<!-- start_list_of_recent_updated_pages -->\n")
        i = 0
        for filename in get_latest_update():
            if filename[0] == "_": continue
            pagename=filename.split(".")[0]
            #print(pagename)
            f.write("* [["+pagename+"]]\n")
            i += 1
            if i >= 10: break
        f.write("<!-- end_list_of_recent_updated_pages -->\n")


def main(list_of_pages, list_of_illegal_pages):
    for filename in os.listdir(dir):
        if filename == ".git" : continue

        pagename = filename.split("/")[-1]
        pagename = pagename.split(".")[0]
        #print("main:"+pagename)


        # 自動リンク
        add_auto_link(filename, list_of_pages)
        # ページの目次を生成
        generate_index_of_page(filename)
        # 子ページの一覧を生成
        generate_index_of_child_pages(filename, list_of_pages)
        # 違反ページ一覧を生成
        generate_list_of_illegal_pages(filename, list_of_illegal_pages)



if __name__=="__main__":
    list_of_pages, list_of_illegal_pages = preprocess()
    # sidebarを作る
    generate_sidebar(list_of_pages)
    
    main(list_of_pages, list_of_illegal_pages)
