#!/usr/bin/env python3
import re
from pathlib import Path
from typing import Dict, Tuple


def remove_markdown_syntax(text: str) -> str:
    """マークダウン記法を削除してプレーンテキストを取得"""
    # コードブロックを削除
    text = re.sub(r"```[\s\S]*?```", "", text)
    # インラインコードを削除
    text = re.sub(r"`[^`]*`", "", text)
    # リンクを削除 [text](url) -> text
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # 画像を削除 ![alt](url)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    # 見出しの#を削除
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    # 装飾記号を削除（*、_、~）
    text = re.sub(r"[*_~]{1,2}([^*_~]*)[*_~]{1,2}", r"\1", text)
    # HTML要素を削除
    text = re.sub(r"<[^>]+>", "", text)
    return text


def count_words_in_file(file_path: Path) -> Tuple[int, int]:
    """ファイルの単語数をカウント。(全体の単語数, 実質的な単語数)を返す"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # 全体の単語数（マークダウン記法を含む）
            raw_words = len(re.findall(r"\S+", content))
            # マークダウン記法を除いた実質的な単語数
            plain_text = remove_markdown_syntax(content)
            effective_words = len(re.findall(r"\S+", plain_text))
            return raw_words, effective_words
    except Exception as e:
        print(f"エラー: {file_path} の読み込み中にエラーが発生しました - {e}")
        return 0, 0


def count_markdown_files(doc_dir: str) -> Dict[str, Tuple[int, int]]:
    """docディレクトリ内のマークダウンファイルの単語数をカウント"""
    results = {}
    doc_path = Path(doc_dir)

    if not doc_path.exists():
        print(f"エラー: {doc_dir} が見つかりません")
        return results

    for md_file in doc_path.glob("**/*.md"):
        relative_path = str(md_file.relative_to(doc_path))
        raw_count, effective_count = count_words_in_file(md_file)
        results[relative_path] = (raw_count, effective_count)

    return results


def main():
    doc_dir = "doc"
    results = count_markdown_files(doc_dir)

    if not results:
        print("マークダウンファイルが見つかりませんでした")
        return

    print("\nマークダウンファイルの単語数統計:")
    print("-" * 80)
    print(f"{'ファイル名':<40} {'全体単語数':>15} {'実質単語数':>15}")
    print("-" * 80)

    total_raw = 0
    total_effective = 0

    for file_path, (raw_count, effective_count) in sorted(results.items()):
        print(f"{file_path:<40} {raw_count:>15,d} {effective_count:>15,d}")
        total_raw += raw_count
        total_effective += effective_count

    print("-" * 80)
    print(f"{'合計:':<40} {total_raw:>15,d} {total_effective:>15,d}")


if __name__ == "__main__":
    main()
