# Phase 2〜4：Sites-lite、Gemini鑑定、コンテンツ品質パイプライン

このExecPlanは、`infinite-arcana-requirements-design.md` のPhase 2〜4を、既存のPhase 0/1成果物へ接続するための実装記録である。実装中は `Progress`、`Surprises & Discoveries`、`Decision Log`、`Outcomes & Retrospective` を更新する。

## Purpose / Big Picture

ブラウザだけで抽選・公開・図鑑・履歴を体験できるSites-liteを作り、鑑定が必要な場合だけサーバー側のGeminiへ接続する。APIキーはブラウザへ渡さず、Geminiが利用できない場合でもカード定義由来の定型解釈を返す。さらにPython CLIでコンテンツの参照整合性、テーマ継承、重複、ローカル画像のハッシュを検査し、再現可能なリリースmanifestを出力する。

## Progress

- [x] (2026-07-26) Sites-liteの静的UI、抽選、カード公開、図鑑、履歴、IndexedDB/localStorageフォールバック、JSON入出力を実装した。
- [x] (2026-07-26) Python共通エンジンとブラウザ抽選エンジンで、同一seedのテストベクトルを一致させた。
- [x] (2026-07-26) Gemini構造化出力の入力制限、JSON検証、再試行、タイムアウト、定型フォールバックを実装した。
- [x] (2026-07-26) `google-genai` をサーバー側オプション依存として宣言し、`.env.example` に無料枠モデル設定を記載した。
- [x] (2026-07-26) Python品質CLIとリリースmanifest生成を実装し、現行22カード・22原型・3スプレッド・24アセットを検査した。
- [x] (2026-07-26) Gemini互換の候補生成CLI、バッチ定義、類似度レポート、人手レビュー記録CLIを追加した。
- [x] (2026-07-26) Node.js Ajv検証、Python unittest、ブラウザengineテスト、Sites-liteビルドを通過させた。

## Surprises & Discoveries

- Observation: 実行環境にFastAPIとGemini SDKが必ずしも存在しない。
  Evidence: 依存を追加しなくても検証できるよう、APIの薄いHTTPアダプターは標準ライブラリで実装し、Gemini SDKは`requirements.txt`の任意依存として遅延importする設計にした。
- Observation: Sites-liteのビルド成果物からはリポジトリルートの`packages/content`を直接参照できない。
  Evidence: ビルド時にコンテンツと画像を`apps/sites-lite/dist/content`、`dist/assets`へコピーし、asset catalogのbasePathを`assets`へ書き換える必要がある。
- Observation: 無料枠やモデル名はGoogle側で変動し得る。
  Evidence: モデル名を環境変数で上書きできるようにし、デフォルトは`gemini-3.1-flash-lite`、キー未設定時は必ず定型フォールバックとした。
- Observation: 候補の意味的な類似度を完全自動判定すると、正当なバリエーションを落とす可能性がある。
  Evidence: 類似度レポートはJaccardスコアと`reviewRequired`だけを出し、公開判断はレビュー記録の`approved`に残す設計にした。

## Decision Log

- Decision: Sites-liteはPythonバックエンドを必須にせず、静的配布を基本とする。
  Rationale: Phase 2のLLMなし体験を無料・低コストで検証でき、通常版APIの実装をPhase 5へ遅延できるため。
- Decision: Gemini呼び出しは`GoogleGenaiClient`へ隔離し、`response_mime_type=application/json`とschema-bound responseを使用する。
  Rationale: 自由文をアプリへ直接渡さず、カードID・正逆・要約などの出力契約を検証できるため。
- Decision: 品質レポートとrelease manifestは生成物として`artifacts/`へ出力し、入力JSON・画像台帳をハッシュ対象にする。
  Rationale: Gitへ時刻依存の生成物を常時コミットせず、同じリリース入力から差分を検出できるため。
- Decision: 生成候補は公開manifestへ直接追加せず、バッチ出力とレビュー記録を経由させる。
  Rationale: `published`への人手承認を必須とする要件を守り、Geminiの生成物を実行時コンテンツへ混入させないため。

## Plan of Work

1. `packages/core`のコンテンツローダー、seed抽選、スプレッド、鑑定記録をPython標準ライブラリで維持する。
2. `apps/sites-lite`を静的ビルドし、`packages/content`とWebPを同梱する。カード公開前は共通裏面を表示する。
3. `apps/api/interpreter.py`でGeminiの構造化出力を検証し、失敗時は定型結果へ戻す。`server.py`はAPIキーをクライアントへ返さない。
4. `tools/content_pipeline/validate_content.py`でテーマ継承、名前重複、ローカルアセット、SHA-256を検査し、release manifestを生成する。
5. Node/Python/ブラウザテストとSites-liteビルドを実行し、受け入れ条件の証跡を残す。

## Validation and Acceptance

- `npm.cmd run validate:content` が成功する。
- `python -m unittest discover -s tests -v` と `node --test apps/sites-lite/test/engine.test.mjs` が成功する。
- `npm.cmd run content:quality` がエラー0件で、release manifestの各ファイルに64文字のSHA-256を持つ。
- `npm.cmd run sites:build` が成功し、WebP、コンテンツ、UIが`apps/sites-lite/dist`へ配置される。
- APIキー文字列がブラウザJS、静的成果物、鑑定レスポンスへ混入しない。
- Gemini SDK未導入・キー未設定・不正JSON・タイムアウト時に定型結果で応答する。

## Outcomes & Retrospective

Phase 2〜4の実装と検証を完了した。Phase 5（認証、DB、複数端末同期、決済、運営画面）は今回の範囲外であり、Sites-liteの静的配布とサーバー側Gemini境界を再利用して進められる。

## Interfaces and Dependencies

- Python: 標準ライブラリ。Geminiを使用する場合のみ`requirements.txt`の`google-genai`をインストールする。
- Node.js: Ajvによる既存JSON Schema検証。
- Browser: Web Crypto API、IndexedDB（フォールバックlocalStorage）。
- External: Google Gemini API（サーバー側のみ、`GEMINI_API_KEY`）。
