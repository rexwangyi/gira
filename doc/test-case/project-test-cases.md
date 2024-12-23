# プロジェクト管理画面テストケース

| テストケース ID | テスト項目                               | 前提条件               | 入力値                     | 期待結果                         |
| --------------- | ---------------------------------------- | ---------------------- | -------------------------- | -------------------------------- |
| TC_PROJECT_001  | 正常系: プロジェクト作成                 | -                      | プロジェクト名、説明       | プロジェクトが作成され一覧に表示 |
| TC_PROJECT_002  | 異常系: 名前未入力                       | -                      | 説明のみ                   | 入力必須エラーメッセージを表示   |
| TC_PROJECT_003  | 正常系: プロジェクト編集                 | プロジェクトが存在     | 新しいプロジェクト名、説明 | プロジェクト情報が更新される     |
| TC_PROJECT_004  | 異常系: 編集時の名前重複                 | 同名プロジェクトが存在 | 重複するプロジェクト名     | エラーメッセージを表示           |
| TC_PROJECT_005  | 異常系: 説明未入力                       | -                      | プロジェクト名のみ         | 入力必須エラーメッセージを表示   |
| TC_PROJECT_006  | 正常系: プロジェクト削除                 | プロジェクトが存在     | プロジェクトを削除         | プロジェクトが一覧から削除される |
| TC_PROJECT_007  | 異常系: プロジェクト削除失敗             | プロジェクトが存在     | プロジェクトを削除         | エラーメッセージを表示           |
| TC_PROJECT_008  | 正常系: プロジェクトのステータス変更     | プロジェクトが存在     | ステータスを変更           | ステータスが正しく反映される     |
| TC_PROJECT_009  | 異常系: プロジェクトのステータス変更失敗 | プロジェクトが存在     | ステータスを変更           | エラーメッセージを表示           |