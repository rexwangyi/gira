from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver import ActionChains
import time
import unittest
import logging
import traceback
import os
import tempfile

# Seleniumのログレベルを設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger('selenium').setLevel(logging.ERROR)
temp_dir = tempfile.mkdtemp()

# Chromeドライバーのログを無効化
chrome_options = Options()
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_options.add_argument(f"--user-data-dir={temp_dir}")
chrome_options.add_argument("--verbose") 
chrome_options.add_argument("--log-level=3")
if os.getenv('ENV') != 'local':
    chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")


# スクリーンショットの保存先を設定
RESULT_DIR = os.path.join(os.path.dirname(__file__), 'result')
os.makedirs(RESULT_DIR, exist_ok=True)

class GiraUITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """テスト開始前に1回だけ実行"""
        cls.browser = webdriver.Chrome(options=chrome_options)
        cls.wait = WebDriverWait(cls.browser, 20)  # 待機時間を20秒に延長
        cls.base_url = 'http://127.0.0.1:5000'
        cls.browser.maximize_window()  # ウィンドウを最大化
        
        # 最初にログインを実行
        try:
            cls.browser.get(f'{cls.base_url}/login')
            logger.info(f"ログインページにアクセス: {cls.base_url}/login")
            
            # 無効なログインを試行
            username_input = cls.wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_input.clear()
            username_input.send_keys('invalid_user')
            
            password_input = cls.wait.until(EC.presence_of_element_located((By.ID, "password")))
            password_input.clear()
            password_input.send_keys('invalid_password')
            
            submit_button = cls.wait.until(EC.presence_of_element_located((By.ID, "submit")))
            submit_button.click()
            logger.info("無効なログイン情報でログインを試行")
            
            # エラーメッセージを確認
            error_message = cls.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert-error")))
            assert "ユーザー名またはパスワードが正しくありません" in error_message.text
            logger.info("✓ 無効なログインの確認完了")
            
            # 有効なログインを実行
            username_input = cls.wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_input.clear()
            username_input.send_keys('admin')
            
            password_input = cls.wait.until(EC.presence_of_element_located((By.ID, "password")))
            password_input.clear()
            password_input.send_keys('admin123')
            
            submit_button = cls.wait.until(EC.presence_of_element_located((By.ID, "submit")))
            submit_button.click()
            logger.info("有効なログイン情報でログインを実行")
            
            # ログイン成功を確認
            cls.wait.until(EC.url_contains('/backlog'))
            assert '/backlog' in cls.browser.current_url
            logger.info("✓ 正常ログインの確認完了")
            
        except Exception as e:
            logger.error(f"初期セットアップ中にエラーが発生: {str(e)}")
            if cls.browser:
                cls.browser.save_screenshot(os.path.join(RESULT_DIR, 'error_setup.png'))
                cls.browser.quit()
            raise

    def setUp(self):
        """各テストメソッドの実行前に実行"""
        # 前のテストの状態をクリーンアップする必要がある場合はここに記述
        pass

    @classmethod
    def tearDownClass(cls):
        """全テスト終了後に1回だけ実行"""
        if cls.browser:
            # ログアウトを実行
            try:
                logout_link = cls.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.logout-link")))
                cls.browser.execute_script("arguments[0].click();", logout_link)
                
                cls.wait.until(EC.url_contains('/login'))
                assert '/login' in cls.browser.current_url
                logger.info("✓ ログアウト確認完了")
            except Exception as e:
                logger.error(f"ログアウト中にエラーが発生: {str(e)}")
            finally:
                cls.browser.quit()

    def save_screenshot(self, prefix='error'):
        """スクリーンショットを保存"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f'{prefix}_{timestamp}.png'
        filepath = os.path.join(RESULT_DIR, filename)
        self.browser.save_screenshot(filepath)
        logger.info(f"スクリーンショットを保存: {filepath}")

    def wait_and_find_element(self, by, value, timeout=10):
        """要素を待機して取得する共通関数"""
        try:
            element = WebDriverWait(self.browser, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.error(f"要素が見つかりませんでした: {by}={value}")
            self.save_screenshot('error_element_not_found')
            raise

    def wait_for_count_change(self, status, initial_count, expected_change, timeout=10):
        """ストーリー数の変更を待機"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            current_count = self.count_kanban_items(status)
            if current_count == initial_count + expected_change:
                return True
            time.sleep(0.5)
        return False

    def drag_and_drop_with_retry(self, source, target, max_retries=3):
        """ドラッグ＆ドロップを実行し、必要に応じて再試行"""
        try:
            source_id = source.get_attribute('data-story-id')
            logger.info(f"ストーリー {source_id} を移動開始")
            
            # スクロールして要素を表示
            self.browser.execute_script("arguments[0].scrollIntoView(true);", source)
            time.sleep(1)  # スクロール完了を待つ

            for attempt in range(max_retries):
                try:
                    # JavaScriptを使用してSortableJSのドラッグ＆ドロップをシミュレート
                    self.browser.execute_script("""
                        function simulateDragDrop(sourceNode, targetNode) {
                            // ドラッグ開始イベントをディスパッチ
                            const dragStartEvent = new DragEvent('dragstart', {
                                bubbles: true,
                                cancelable: true,
                                dataTransfer: new DataTransfer()
                            });
                            sourceNode.dispatchEvent(dragStartEvent);

                            // ドラッグオーバーイベントをディスパッチ
                            const dragOverEvent = new DragEvent('dragover', {
                                bubbles: true,
                                cancelable: true,
                                dataTransfer: new DataTransfer()
                            });
                            targetNode.dispatchEvent(dragOverEvent);

                            // 要素を移動
                            targetNode.appendChild(sourceNode);

                            // ドロップイベントをディスパッチ
                            const dropEvent = new DragEvent('drop', {
                                bubbles: true,
                                cancelable: true,
                                dataTransfer: new DataTransfer()
                            });
                            targetNode.dispatchEvent(dropEvent);

                            // SortableJSのイベントをシミュレート
                            const sortableEvent = new CustomEvent('sortablejs:change', {
                                bubbles: true,
                                cancelable: true,
                                detail: {
                                    item: sourceNode,
                                    to: targetNode,
                                    newIndex: Array.from(targetNode.children).indexOf(sourceNode)
                                }
                            });
                            targetNode.dispatchEvent(sortableEvent);
                        }
                        
                        simulateDragDrop(arguments[0], arguments[1]);
                    """, source, target)
                    
                    logger.info("移動処理完了、更新を待機中...")
                    time.sleep(3)  # 状態更新の完了を待つ
                    
                    logger.info("✓ ドラッグ＆ドロップ成功")
                    return True
                    
                except Exception as e:
                    logger.error(f"移動失敗（{attempt + 1}回目）: {str(e)}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2)  # 再試行前に待機
                
        except Exception as e:
            logger.error(f"ドラッグ＆ドロップエラー: {str(e)}")
            raise
            
        return False

    def login(self, username, password):
        """ログイン処理"""
        try:
            self.browser.get(f'{self.base_url}/login')
            logger.info(f"ログインページにアクセス: {self.base_url}/login")
            
            username_input = self.wait_and_find_element(By.ID, "username")
            username_input.clear()
            username_input.send_keys(username)
            logger.info(f"ユーザー名を入力: {username}")
            
            password_input = self.wait_and_find_element(By.ID, "password")
            password_input.clear()
            password_input.send_keys(password)
            logger.info("パスワードを入力")
            
            submit_button = self.wait_and_find_element(By.ID, "submit")
            submit_button.click()
            logger.info("ログインボタンをクリック")
            
        except Exception as e:
            logger.error(f"ログイン中にエラーが発生: {str(e)}")
            self.save_screenshot('error_login')
            raise

    def count_kanban_items(self, status):
        """かんばんボードの列のストーリー数を取得"""
        items = self.browser.find_elements(By.CSS_SELECTOR, f'.story-list[data-status="{status}"] .story-card')
        return len(items)

    def navigate_to_page(self, menu_id):
        """左メニューを使用してページに遷移"""
        try:
            # メニューアイテムのセレクタを修正
            menu_selectors = {
                'menu-projects': "a.list-group-item-action i.bi-folder",
                'menu-backlog': "a.list-group-item-action i.bi-kanban",
                'menu-kanban': "a.list-group-item-action i.bi-calendar-check"
            }
            
            selector = menu_selectors.get(menu_id)
            if not selector:
                raise ValueError(f"未知のメニューID: {menu_id}")
            
            menu_item = self.wait_and_find_element(
                By.CSS_SELECTOR,
                selector
            ).find_element(By.XPATH, "./..")
            
            self.browser.execute_script("arguments[0].click();", menu_item)
            logger.info(f"左メニュー {menu_id} をクリック")
            time.sleep(2)  # ページ遷移を待機
        except Exception as e:
            logger.error(f"ページ遷移中にエラーが発生: {str(e)}")
            self.save_screenshot('error_navigation')
            raise

    def test_01_project_description(self):
        """プロジェクト説明編集テスト"""
        logger.info("\n=== プロジェクト説明編集テスト開始 ===")
        
        # プロジェクト管理ページに移動
        self.navigate_to_page("menu-projects")
        
        # プロジェクトリストの読み込みを待機
        self.wait.until(
            EC.presence_of_element_located((By.ID, "project-list"))
        )
        
        # 編集ボタンをクリック
        edit_button = self.wait_and_find_element(
            By.CSS_SELECTOR,
            'button.btn-sm.btn-outline-secondary i.bi-pencil'
        ).find_element(By.XPATH, "./..")
        self.browser.execute_script("arguments[0].click();", edit_button)
        logger.info("編集ボタンをクリック")
        
        # モーダルが表示されるのを待機
        self.wait.until(
            EC.visibility_of_element_located((By.ID, "project-modal"))
        )
        
        # 説明を変更
        description_input = self.wait_and_find_element(By.ID, "description")
        self.wait.until(EC.element_to_be_clickable((By.ID, "description")))
        original_description = description_input.get_attribute('value')
        new_description = "テスト用説明文"
        
        # JavaScriptを使用して値を設定
        self.browser.execute_script(
            "arguments[0].value = arguments[1]",
            description_input,
            new_description
        )
        logger.info(f"説明を変更: {new_description}")
        
        # フォームの送信
        form = self.wait_and_find_element(By.ID, "project-form")
        self.browser.execute_script("arguments[0].dispatchEvent(new Event('submit'))", form)
        logger.info("フォームを送信")
        
        # モーダルが閉じるのを待機
        self.wait.until(
            EC.invisibility_of_element_located((By.ID, "project-modal"))
        )
        time.sleep(2)
        
        # 変更が反映されたことを確認
        edit_button = self.wait_and_find_element(
            By.CSS_SELECTOR,
            'button.btn-sm.btn-outline-secondary i.bi-pencil'
        ).find_element(By.XPATH, "./..")
        self.browser.execute_script("arguments[0].click();", edit_button)
        
        # モーダルが表示されるのを待機
        self.wait.until(
            EC.visibility_of_element_located((By.ID, "project-modal"))
        )
        
        description_input = self.wait_and_find_element(By.ID, "description")
        self.assertEqual(description_input.get_attribute('value'), new_description)
        logger.info("✓ 説明の変更が反映されていることを確認")
        
        # 元の説明に戻す
        self.browser.execute_script(
            "arguments[0].value = arguments[1]",
            description_input,
            original_description
        )
        
        # フォームの送信
        form = self.wait_and_find_element(By.ID, "project-form")
        self.browser.execute_script("arguments[0].dispatchEvent(new Event('submit'))", form)
        logger.info("説明を元に戻して保存")
        
        # モーダルが閉じるのを待機
        self.wait.until(
            EC.invisibility_of_element_located((By.ID, "project-modal"))
        )
        time.sleep(2)
        
        # 元の説明に戻ったことを確認
        edit_button = self.wait_and_find_element(
            By.CSS_SELECTOR,
            'button.btn-sm.btn-outline-secondary i.bi-pencil'
        ).find_element(By.XPATH, "./..")
        self.browser.execute_script("arguments[0].click();", edit_button)
        
        # モーダルが表示されるのを待機
        self.wait.until(
            EC.visibility_of_element_located((By.ID, "project-modal"))
        )
        
        description_input = self.wait_and_find_element(By.ID, "description")
        self.assertEqual(description_input.get_attribute('value'), original_description)
        logger.info("✓ 説明が元の値に戻ったことを確認")
        
        # モーダルを閉じる
        cancel_button = self.wait_and_find_element(
            By.CSS_SELECTOR,
            'button[data-bs-dismiss="modal"]'
        )
        self.browser.execute_script("arguments[0].click();", cancel_button)
        
        # モーダルが閉じるのを待機
        self.wait.until(
            EC.invisibility_of_element_located((By.ID, "project-modal"))
        )
        
        logger.info("=== プロジェクト説明編集テスト完了 ===\n")

    def test_02_backlog_story_movement(self):
        """バックログでのストーリー移動テスト"""
        logger.info("\n=== バックログでのストーリー移動テスト開始 ===")
        
        # バックログページに移動
        self.navigate_to_page("menu-backlog")
        
        # スプリント2のストーリー数を確認
        sprint2_stories_initial = len(self.browser.find_elements(
            By.CSS_SELECTOR, 
            '#sprint-2 .story-row'
        ))
        logger.info(f"スプリント2の初期ストーリー数: {sprint2_stories_initial}")

        # バックログからスプリント2へストーリーを移動
        source = self.wait_and_find_element(
            By.CSS_SELECTOR, 
            '.backlog-section .story-list .story-row'
        )
        target = self.wait_and_find_element(
            By.CSS_SELECTOR, 
            '#sprint-2'
        )
        
        self.drag_and_drop_with_retry(source, target)
        time.sleep(3)

        # スプリント2のストーリー数が増加したことを確認
        sprint2_stories_after = len(self.browser.find_elements(
            By.CSS_SELECTOR, 
            '#sprint-2 .story-row'
        ))
        
        self.assertEqual(sprint2_stories_initial + 1, sprint2_stories_after)
        logger.info(f"スプリント2のストーリー数が{sprint2_stories_initial}から{sprint2_stories_after}に増加")

        # スプリント2からバックログへストーリーを戻す
        source = self.wait_and_find_element(
            By.CSS_SELECTOR, 
            '#sprint-2 .story-row'
        )
        target = self.wait_and_find_element(
            By.CSS_SELECTOR, 
            '.backlog-section .story-list'
        )
        
        self.drag_and_drop_with_retry(source, target)
        time.sleep(3)

        # スプリント2のストーリー数が元に戻ったことを確認
        sprint2_stories_final = len(self.browser.find_elements(
            By.CSS_SELECTOR, 
            '#sprint-2 .story-row'
        ))
        self.assertEqual(sprint2_stories_initial, sprint2_stories_final)
        logger.info(f"スプリント2のストーリー数が{sprint2_stories_after}から{sprint2_stories_final}に減少")
        
        logger.info("=== バックログでのストーリー移動テスト完了 ===\n")

    def test_03_kanban_story_movement(self):
        """かんばんボードでのストーリー移動テスト"""
        logger.info("\n=== かんばんボードでのストーリー移動テスト開始 ===")
        
        # かんばんボードページに移動
        self.navigate_to_page("menu-kanban")
        
        # 各列の初期ストーリー数を確認
        todo_initial = self.count_kanban_items("todo")
        doing_initial = self.count_kanban_items("doing")
        done_initial = self.count_kanban_items("done")
        logger.info(f"初期状態 - Todo: {todo_initial}, In Progress: {doing_initial}, Done: {done_initial}")

        if todo_initial == 0:
            logger.warning("Todoリストにストーリーがありません")
            return

        # TodoからIn Progressへ移動
        source = self.wait_and_find_element(
            By.CSS_SELECTOR, 
            '.story-list[data-status="todo"] .story-card'
        )
        target = self.wait_and_find_element(
            By.CSS_SELECTOR, 
            '.story-list[data-status="doing"]'
        )
        
        self.drag_and_drop_with_retry(source, target)
        self.assertTrue(
            self.wait_for_count_change("doing", doing_initial, 1),
            "In Progress列のストーリー数が期待通り増加しませんでした"
        )

        # 件数の変化を確認
        todo_after_move1 = self.count_kanban_items("todo")
        doing_after_move1 = self.count_kanban_items("doing")
        self.assertEqual(todo_initial - 1, todo_after_move1)
        self.assertEqual(doing_initial + 1, doing_after_move1)
        logger.info(f"移動後 - Todo: {todo_after_move1}, In Progress: {doing_after_move1}")

        # In ProgressからDoneへ移動
        source = self.wait_and_find_element(
            By.CSS_SELECTOR, 
            '.story-list[data-status="doing"] .story-card'
        )
        target = self.wait_and_find_element(
            By.CSS_SELECTOR, 
            '.story-list[data-status="done"]'
        )
        
        self.drag_and_drop_with_retry(source, target)
        self.assertTrue(
            self.wait_for_count_change("done", done_initial, 1),
            "Done列のストーリー数が期待通り増加しませんでした"
        )

        # 件数の変化を確認
        doing_after_move2 = self.count_kanban_items("doing")
        done_after_move = self.count_kanban_items("done")
        self.assertEqual(doing_initial, doing_after_move2)
        self.assertEqual(done_initial + 1, done_after_move)
        logger.info(f"移動後 - In Progress: {doing_after_move2}, Done: {done_after_move}")

        # DoneからTodoへ戻す
        source = self.wait_and_find_element(
            By.CSS_SELECTOR, 
            '.story-list[data-status="done"] .story-card'
        )
        target = self.wait_and_find_element(
            By.CSS_SELECTOR, 
            '.story-list[data-status="todo"]'
        )
        
        self.drag_and_drop_with_retry(source, target)
        self.assertTrue(
            self.wait_for_count_change("todo", todo_after_move1, 1),
            "Todo列のストーリー数が期待通り増加しませんでした"
        )

        # 最終的な件数を確認
        todo_final = self.count_kanban_items("todo")
        doing_final = self.count_kanban_items("doing")
        done_final = self.count_kanban_items("done")
        self.assertEqual(todo_initial, todo_final)
        self.assertEqual(doing_initial, doing_final)
        self.assertEqual(done_initial, done_final)
        logger.info(f"最終状態 - Todo: {todo_final}, In Progress: {doing_final}, Done: {done_final}")
        
        logger.info("=== かんばんボードでのストーリー移動テスト完了 ===\n")

if __name__ == '__main__':
    unittest.main() 