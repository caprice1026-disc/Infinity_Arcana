# React と Python で Sites Lite MVP を実装する

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository contains `PLANS.md` at the repository root. This document must be maintained in accordance with `PLANS.md` whenever implementation progress, discoveries, or design decisions change. A contributor must be able to resume the work using only this file and the current repository tree.

## Purpose / Big Picture

この計画の目的は、現在JSONコンテンツとカード画像を中心に構成されている Infinity Arcana を、実際にブラウザで操作できる最小製品へ進めることである。完成後、利用者は相談内容を入力し、カード裏面が画面上を移動して配置され、カードが反転して正位置または逆位置のアルカナが表示され、まずは静的な鑑定文を読める。ブラウザを再読み込みしても鑑定履歴と発見済みカードが保存される。さらに、Python製APIを起動した場合は同じ抽選結果を使ってLLM鑑定を取得できる。

技術構成は、画面とブラウザ内処理を React、TypeScript、Vite で実装し、LLM鑑定と将来の認証、課金、サーバー保存を Python、FastAPI、Pydantic で実装する。カード抽選は Sites Lite がAPIなしでも動作できるよう TypeScript の純粋な共通パッケージに置く。コンテンツの正本は既存の `packages/content` と `packages/schemas` に置き続け、抽選をLLMへ委ねない。

この計画は、現時点の22枚を使った1枚引きMVPを最初の到達点とする。66枚以上への拡張、3枚引き、ログイン、PostgreSQL、課金は、1枚引き体験と契約が安定した後に進める。

## Progress

- [x] (2026-07-22) 既存の要件設計、コンテンツ構造、アセットカタログ、検証ツール、`PLANS.md`を確認した。
- [x] (2026-07-22) ReactとPythonを組み合わせる責務分離を決定した。
- [x] (2026-07-22) `cards/babel-library/card-knowledge-arcana-vol-1-back-v1.png` をパック共通カード裏面として扱う方針を決定した。
- [ ] Milestone 1: モノレポの基盤、Reactアプリ、TypeScript共通コア、FastAPIアプリの空構成を追加する。
- [ ] Milestone 2: パック共通カード裏面を正式なアセットとして登録し、変換、参照、検証、テストを実装する。
- [ ] Milestone 3: スプレッド、抽選要求、抽選結果、鑑定記録、鑑定APIの契約を追加する。
- [ ] Milestone 4: seed付き決定論的乱数と `balanced-two-stage-v1` 抽選をTypeScriptで実装する。
- [ ] Milestone 5: Reactで1枚引き、裏面移動、反転、正逆表示、静的鑑定を実装する。
- [ ] Milestone 6: IndexedDBへ履歴と図鑑を保存し、再読み込み後も復元できるようにする。
- [ ] Milestone 7: FastAPIのモック鑑定APIとLLMプロバイダー境界を実装する。
- [ ] Milestone 8: OpenAI等のLLMプロバイダーを接続し、静的鑑定へのフォールバックを実装する。
- [ ] Milestone 9: READMEを現状に合わせて更新し、セットアップ、技術構成、実装状況、アセット状況を明記する。
- [ ] Milestone 10: 単体、結合、E2EテストとGitHub Actionsを整備し、MVPの受け入れを完了する。

## Surprises & Discoveries

- Observation: 現在のルート `package.json` はコンテンツ検証とBabel Libraryの前面画像ビルドだけを持ち、WebアプリやAPIの依存関係をまだ持っていない。
  Evidence: `package.json` のスクリプトは `validate:content` と `assets:build:babel-library` のみである。このため、npm workspacesを追加しても既存処理への移行負荷は小さい。

- Observation: アセットスキーマはすでに `card-back` を種類として許可しているが、現在のビルドスクリプトは `card-front` だけを処理する。
  Evidence: `packages/schemas/asset-catalog.schema.json` と `tools/build-babel-library-assets.mjs` の責務が非対称である。裏面対応では新しいスキーマ種類を作るのではなく、既存種類をビルドと検証へ接続する。

- Observation: カードJSONには任意の `visual.cardBackAssetId` がある一方、パックJSONには共通裏面の参照がない。
  Evidence: 現在追加された裏面画像は `knowledge-arcana-vol-1` 全体で共通利用する意図である。全カードへ同じIDを複製すると更新漏れが生じるため、パック共通値とカード単位overrideを分ける必要がある。

- Observation: READMEには画像が未作成である趣旨の記述が残っているが、前面画像と今回の裏面画像が存在する。
  Evidence: READMEを単なる後処理ではなく、実装状況を正確に伝える成果物として更新する必要がある。

## Decision Log

- Decision: フロントエンドは React、TypeScript、Vite を使用する。
  Rationale: このアプリの中心はカード操作、アニメーション、ローカル履歴を持つSPAであり、サーバー描画を必須としない。TypeScriptによりカード、抽選結果、状態遷移を型で固定できる。
  Date/Author: 2026-07-22 / OpenAI

- Decision: バックエンドは Python 3.12以降、FastAPI、Pydantic、uv、Ruff、Pyright、pytestを使用する。
  Rationale: PythonをLLM接続、API入力検証、将来の認証と永続化、コンテンツ生成補助に集中させる。FastAPIのOpenAPIを利用してTypeScript APIクライアントを生成できる。
  Date/Author: 2026-07-22 / OpenAI

- Decision: カード抽選の正本実装は `packages/core` のTypeScriptとする。
  Rationale: Sites LiteはPython APIが停止していても抽選と静的鑑定が動く必要がある。抽選をサーバー専用にすると軽量版の要件を満たせない。将来Python版が必要になった場合は同じテストベクトルで互換性を検証する。
  Date/Author: 2026-07-22 / OpenAI

- Decision: 乱数は `Math.random()` を使わず、アルゴリズムIDとバージョンを固定したseed付き疑似乱数を使う。
  Rationale: 同一seed、コンテンツリリース、抽選ポリシー、スプレッド、フィルターから同一結果を再現するためである。
  Date/Author: 2026-07-22 / OpenAI

- Decision: カード裏面はパックを既定値、カードをoverride、アプリを最終fallbackとする。
  Rationale: 今回の裏面は `knowledge-arcana-vol-1` 全体のデザインであり、22カードへの重複記録を避ける。解決順は `card.visual.cardBackAssetId`、`pack.visual.cardBackAssetId`、アプリ組み込み既定画像とする。
  Date/Author: 2026-07-22 / OpenAI

- Decision: 初期状態管理は Reactの `useReducer` とContextを用い、Reduxを導入しない。
  Rationale: 初期MVPの状態は鑑定セッション、アニメーション、設定に限定される。状態機械を明示すれば外部ストアなしで十分に検証可能である。
  Date/Author: 2026-07-22 / OpenAI

- Decision: カードアニメーションは最初にCSS 3D Transformで実装し、アニメーションライブラリを必須依存にしない。
  Rationale: 裏表の反転は `rotateY`、正逆は外側の `rotateZ` で分離できる。要件を満たすためにCanvasやWebGLは不要である。
  Date/Author: 2026-07-22 / OpenAI

- Decision: ブラウザ保存は IndexedDB を使い、Dexieを薄い実装詳細として採用する。
  Rationale: 履歴と図鑑はlocalStorageより構造化データに向く。UIからDexieを直接呼ばず、リポジトリインターフェースを挟むことで将来HTTP実装へ差し替えられる。
  Date/Author: 2026-07-22 / OpenAI

- Decision: APIへカード本文を送らず、ID、contentVersion、contentReleaseIdを送る。
  Rationale: サーバーが信頼済みJSONからカード内容を解決することで、クライアント改変によるプロンプト汚染を避ける。
  Date/Author: 2026-07-22 / OpenAI

- Decision: 履歴には参照IDとハッシュだけでなく、表示に必要な最小スナップショットを保存する。
  Rationale: 将来コンテンツが改訂または廃止されても、過去の鑑定画面を再表示できるようにする。
  Date/Author: 2026-07-22 / OpenAI

## Outcomes & Retrospective

現時点では計画策定まで完了している。実装完了時には、1枚引きがAPIなしで動作し、任意でFastAPI鑑定へ接続でき、リロード後も履歴と図鑑が残り、同じseedで同じカードを再現できる状態を目標とする。各Milestone完了時に、達成内容、残課題、設計変更、検証結果をこの節へ追記する。

## Context and Orientation

リポジトリの中心は、`packages/content` に置かれたJSONコンテンツ、`packages/schemas` に置かれたJSON Schema、`tools/validate-content.mjs` による検証、`tools/build-babel-library-assets.mjs` による画像変換である。`packages/content/manifest.json` は1つのコンテンツリリースを表し、22原型、22カード、1ドメイン、1パック、アセットカタログを束ねる。

`cards/babel-library/card-knowledge-arcana-vol-1-back-v1.png` は新しく追加されたカード裏面の元画像である。この画像はBabel Library専用の前面画像ではなく、`knowledge-arcana-vol-1` パックのカードを伏せて移動させる際に共通利用する。Webで直接配信する画像は元PNGとは分け、アセットビルドによってWebPへ変換して `apps/sites-lite/public/assets/packs/knowledge-arcana-vol-1/card-back.webp` に配置する。

新しいアプリ構成は次の責務を持つ。

`apps/sites-lite` は利用者がブラウザで触るReactアプリである。相談入力、カード配置、反転、静的鑑定、履歴、図鑑を担当する。

`packages/core` はブラウザやReactに依存しないTypeScriptライブラリである。コンテンツの読み込み後の型、seed付き乱数、抽選ポリシー、アセット解決、鑑定記録生成を担当する。DOM、IndexedDB、HTTP、Reactをimportしてはならない。

`apps/api` はFastAPIアプリである。LLM鑑定、入力検証、コンテンツID解決、将来の認証とサーバー保存を担当する。抽選そのものは担当しない。

`packages/api-client` はFastAPIが出力するOpenAPIから生成するTypeScriptクライアントである。APIの型をフロント側で手書き複製しない。

`packages/test-vectors` は言語に依存しないJSON形式の試験入力と期待結果を置く。seed付き乱数や抽選ポリシーをPythonでも再実装する場合、TypeScriptとPythonの両方が同じベクトルを通過することを要求する。

「決定論的」とは、同一入力から常に同一結果を得られる性質を指す。この計画では、seed、乱数アルゴリズムID、コンテンツリリースID、抽選ポリシーID、フィルター、スプレッドIDが同一なら、同一カードと正逆が得られることを意味する。

「静的鑑定」とは、LLMを呼ばず、カードJSONに保存されている意味、光、影、助言、分野別解釈を組み合わせて表示する鑑定である。ネットワークやAPIキーがなくても必ず利用できる。

## Plan of Work

### Milestone 1: モノレポと実行可能な空アプリを作る

ルート `package.json` にnpm workspacesを追加し、既存スクリプトを維持したまま `apps/sites-lite`、`packages/core`、`packages/api-client` をworkspaceとして認識させる。パッケージマネージャーは現在のnpmから変更しない。NodeのバージョンはLTS系列を前提とし、`.nvmrc` または `.node-version` のどちらか一方を追加して固定する。

`apps/sites-lite` はViteのReact TypeScript構成を基礎にする。生成後のサンプル画面は削除し、アプリ名、空の相談入力領域、コンテンツ読み込み状態を表示する最小画面に置き換える。スタイルはCSS ModulesとCSS Custom Propertiesを使い、Tailwindは初期依存へ加えない。

`packages/core` はTypeScriptライブラリとして作成し、`src/index.ts` から公開型をexportする。Vitestを設定し、単純なsanity testを1件追加する。

`apps/api` は `uv init --package` 相当の構成で作成し、`src/infinity_arcana_api/main.py` にFastAPIアプリを置く。`GET /api/health` がHTTP 200と `{"status":"ok"}` を返すようにする。`pyproject.toml` にはFastAPI、Pydantic、Pydantic Settingsを通常依存、pytest、pytest-asyncio、httpx、Ruff、Pyrightを開発依存として定義する。

ルートの開発コマンドは、WebとAPIを別ターミナルで起動できる明示的な形にする。最初からプロセスマネージャーへ依存しない。

このMilestoneの完了条件は、既存の `npm run validate:content` が引き続き成功し、`npm run dev:web` でReact画面が表示され、`uv run fastapi dev` でヘルスAPIが応答し、WebとPythonの単体テストが成功することである。

### Milestone 2: パック共通カード裏面を正式なアセットにする

`packages/schemas/pack.schema.json` に任意の `visual` オブジェクトを追加し、その中へnullableな `cardBackAssetId` を定義する。既存パックとの後方互換性を保つため必須にはしない。`packages/content/packs/knowledge-arcana-vol-1.json` に `visual.cardBackAssetId` を追加し、値を `card-knowledge-arcana-vol-1-back` とする。

`packages/content/asset-catalog.json` に同じIDのアセットを追加し、`kind` を `card-back` とする。ソースパスは `cards/babel-library/card-knowledge-arcana-vol-1-back-v1.png`、公開パスは `apps/sites-lite/public/assets/packs/knowledge-arcana-vol-1/card-back.webp` とする。画像変換後に幅、高さ、バイト数、SHA-256、生成時刻、利用可能状態を更新する。

現在の `tools/build-babel-library-assets.mjs` はfront限定であるため、`tools/build-assets.mjs` へ一般化する。最低限 `card-front`、`card-back`、`pack-cover` を処理でき、アセットカタログに記載したソースと出力先を入力として使う。個別のBabel Libraryスクリプト名を互換aliasとして残してもよいが、正本ロジックを重複させてはならない。

`tools/validate-content.mjs` には、カードoverrideの `cardBackAssetId` が存在し、種類が `card-back` であること、パック共通の `cardBackAssetId` も同様であることを検証する処理を追加する。front、back、coverの種類を取り違えたfixtureを用意し、失敗メッセージに対象IDと期待kindを含める。

`packages/core/src/assets/resolve-card-assets.ts` に、カード裏面の解決関数を追加する。解決順はカードoverride、パック既定、アプリfallbackである。fallbackはテストと開発を止めないために存在するが、本番コンテンツではパック既定を必須運用とする。

このMilestoneの完了条件は、アセットビルド後にWebPが生成され、コンテンツ検証が成功し、誤ったkindを指定したテストが意図したメッセージで失敗し、Reactの開発画面に裏面画像を表示できることである。

### Milestone 3: コンテンツと鑑定の契約を追加する

`packages/schemas/spread.schema.json` を追加し、最初の `single-card` スプレッドと `situation-obstacle-advice` スプレッドを `packages/content/spreads` に追加する。最初のReact画面は `single-card` だけを使うが、3枚引きで契約を壊さないようpositions配列を最初から採用する。

`packages/core/src/contracts` に `DrawRequest`、`DrawResult`、`DrawnCard`、`ReadingRecord`、`CardDisplaySnapshot`、`InterpretationRequestReference` のTypeScript型を置く。JSON SchemaとTypeScript型を完全自動生成することを最初の条件にせず、同じfixtureをAjvとTypeScriptテストで確認することでずれを検出する。

`ReadingRecord` は最低限、レコードID、作成時刻、相談文、任意カテゴリ、locale、seed、乱数アルゴリズムIDとversion、コンテンツリリースID、抽選ポリシーIDとversion、スプレッドIDとversion、フィルター、引いたカード、静的またはLLM鑑定結果を持つ。各カードにはcardIdとcontentVersionに加え、名称、サブタイトル、画像参照、原型名称、位置名称を含む最小表示スナップショットを保存する。

`apps/api` 側には対応するPydanticモデルを作成する。API要求ではカード本文を受け取らず、カードID、card contentVersion、orientation、position ID、content release IDを受ける。`extra="forbid"` を設定し、未定義フィールドを拒否する。

このMilestoneの完了条件は、合法な1枚引きfixtureがJSON Schema、TypeScript、Pydanticのすべてで受理され、未知フィールド、存在しないorientation、空のdrawsが拒否されることである。

### Milestone 4: 決定論的な抽選エンジンを実装する

`packages/core/src/random` に `RandomSource` インターフェースを作り、`nextUint32()`、`nextInt(maxExclusive)`、`algorithmId`、`algorithmVersion`、`seed` を持たせる。アルゴリズムは小さく移植しやすい32bit整数演算のものを1つ選び、IDとversionを固定する。文字列seedから初期状態へ変換する手順も仕様としてコードコメントとテストベクトルに残す。

`nextInt` は単純な剰余ではなくrejection samplingを使い、候補数が2の累乗でない場合の偏りを避ける。候補カードと原型は、JSON読み込み順に依存しないようIDの昇順で並べてから抽選する。

`packages/core/src/draw/policies/balanced-two-stage-v1.ts` に、公開状態、期間、domain、pack、利用権で候補を絞り、原型を均等抽選し、その原型内からカードを均等抽選し、orientationを設定し、使用済みカードと原型を除外する処理を実装する。rarityは初期抽選確率へ影響させない。

描画演出用のランダム値は抽選用RandomSourceから取得しない。カードの揺れや移動方向を変更しても、引かれるカードが変化しないことをテストする。

`packages/test-vectors/seeded-random-v1.json` と `packages/test-vectors/balanced-two-stage-v1.json` を追加し、固定seedの最初の複数出力と抽選結果を記録する。テストベクトルを変更する場合はversionを上げ、既存結果を上書きしない。

このMilestoneの完了条件は、同じ入力を100回実行して同じ結果となること、入力JSONの並び順を変えても結果が変わらないこと、候補数に差がある原型でも原型選択がカード枚数に引きずられないこと、候補不足が型付きエラーとして返ることである。

### Milestone 5: Reactで1枚引き体験を完成させる

`apps/sites-lite/src/features/reading` に相談入力、抽選開始、カード配置、公開、鑑定表示をまとめる。画面遷移をURLごとのページへ分割しすぎず、最初は1つのreading flowとして実装する。React Routerは履歴と図鑑の画面が追加される時点で使用する。

鑑定セッションの状態は判別可能unionとreducerで表現する。最低状態は `idle`、`drawing`、`dealing`、`face-down`、`flipping`、`revealed`、`interpreting`、`completed`、`failed` とする。不正な状態遷移をreducerテストで拒否する。

カードは外側のorientation要素と内側のflip要素へ分ける。外側は逆位置なら `rotateZ(180deg)`、内側は公開時に `rotateY(180deg)` を使う。frontとbackには `backface-visibility: hidden` を設定する。裏面画像はMilestone 2のresolver結果を使う。

最初の演出は、カードの山から1枚が中央へ移動し、短い停止後にクリックまたはボタンで反転する流れとする。シャッフルを巨大な物理シミュレーションにしない。`prefers-reduced-motion: reduce` の利用者には、移動時間をほぼゼロにし、意味のある状態変化は残す。

静的鑑定は `packages/core/src/interpretation/static.ts` に置き、カードJSONのuprightまたはreversed、position、相談カテゴリから構成する。表示は「カード」「この位置での焦点」「光」「影」「次の一歩」のように読みやすい節へ分ける。静的鑑定はネットワークを一切必要としない。

このMilestoneの完了条件は、相談文を入力し、カードを引き、裏面が移動し、反転し、正逆が視覚的に正しく表示され、静的鑑定が現れることである。ブラウザの通信をofflineへ切り替えても同じ流れが完了しなければならない。

### Milestone 6: IndexedDBで履歴と図鑑を保存する

`apps/sites-lite/src/storage` にDexieを使う実装を置くが、featuresからDexieの型を直接参照しない。`packages/core` またはWeb側のapplication境界に `ReadingRepository` と `CollectionRepository` を定義する。

`ReadingRepository` は `save`、`findById`、`listRecent`、`delete`、`exportAll`、`importAll` を持つ。`CollectionRepository` はcardIdごとの初回発見日時、最終発見日時、発見回数、upright回数、reversed回数を保存する。DB schema versionを1から開始し、将来のmigrationをDexie version定義として残す。

履歴一覧、履歴詳細、図鑑一覧の3画面を追加する。履歴詳細は保存したスナップショットを優先し、現在のコンテンツにカードがなくても表示できる。図鑑は未発見カードの名称を隠すかどうかを設定で切り替えられるようにしてもよいが、MVPではカード枠と未発見表示だけでよい。

JSONエクスポートとインポートを追加する。インポート前にschemaVersionを検証し、既存データとの衝突はレコードID単位で上書きまたはskipを選べるようにする。破損したファイルで既存DBを消してはならない。

このMilestoneの完了条件は、1枚引きを行い、画面を再読み込みし、履歴と図鑑に結果が残り、エクスポート後にDBをクリアしてインポートすると同じ履歴が戻ることである。

### Milestone 7: FastAPIのモック鑑定APIを接続する

`apps/api/src/infinity_arcana_api/api/readings.py` に `POST /api/readings/interpret` を追加する。ルートはPydanticで入力を検証し、content release、spread、card、version、orientationをサーバー側コンテンツから解決する。存在しないIDはHTTP 422または404のどちらかに統一し、レスポンス形式をテストで固定する。

`InterpretationProvider` Protocolを作り、最初に `MockInterpretationProvider` と `StaticFallbackInterpretationProvider` を実装する。ルートからプロバイダーSDKを直接呼ばない。サービス層 `InterpretationService` がコンテンツ解決、プロンプト入力構築、プロバイダー呼び出し、構造化結果検証、fallbackを担当する。

CORSは開発用Vite originだけを設定し、ワイルドカードとcredentialの組み合わせを避ける。API URLは `VITE_API_BASE_URL` から読み、未設定またはAPI到達不能なら静的鑑定だけで完了する。

FastAPIのOpenAPI JSONを固定コマンドで出力し、`packages/api-client` の生成コードを更新する。生成物をコミットするか否かは、このMilestoneでビルド環境の再現性を確認してDecision Logへ記録する。どちらを選んでも、CIで生成差分を検出する。

このMilestoneの完了条件は、APIを起動した状態ではMock由来の鑑定が表示され、APIを停止するとエラー画面ではなく静的鑑定へ戻り、改変したカード本文をクライアントから送信できないことである。

### Milestone 8: LLM鑑定を安全に追加する

`apps/api/src/infinity_arcana_api/providers/openai.py` のようなプロバイダー実装を追加する。APIキーは環境変数から読み、ブラウザへ渡さない。プロンプトには相談内容、任意カテゴリ、position意味、原型の中心意味、カード固有の象徴、光、影、助言、orientation、reversedMode、locale、口調、安全制約を渡す。抽選をLLMへ依頼する文言を含めない。

レスポンスはPydanticモデルに適合する構造化出力とし、見出し、要約、positionごとの解釈、行動提案、注意書きを持つ。医療、法律、投資などの高リスク相談では断定を避け、専門家への確認を促すルールをサービス層で付与する。

タイムアウト、rate limit、構造不正、プロバイダー障害を明示的に扱う。短い再試行を1回まで行い、それでも失敗したら静的鑑定へfallbackする。相談文と生成結果をログへ全文出力しない。開発ログにはrequest ID、provider、model、latency、結果種別だけを記録する。

このMilestoneの完了条件は、正常時にLLM鑑定が表示され、無効APIキー、タイムアウト、構造不正のテストでは静的鑑定が表示され、カード抽選結果がAPI呼び出しの成功失敗で変わらないことである。

### Milestone 9: READMEを現状と実装方法に合わせて更新する

ルート `README.md` を更新し、最低限次の内容を含める。

最初に、Infinity Arcanaが架空アルカナを使うブラウザ占いアプリであること、現在の実装段階、最初の利用者体験を説明する。次に、技術構成として React、TypeScript、Vite、TypeScript core、IndexedDB、Dexie、Python、FastAPI、Pydantic、uv、既存JSON Schemaを記載し、それぞれの責務を短く示す。

Repository Structure節を現行ツリーへ合わせ、`apps/sites-lite`、`apps/api`、`packages/core`、`packages/api-client`、`packages/content`、`packages/schemas`、`packages/test-vectors`、`tools`、`.agent` を説明する。

Getting Started節では、Node、npm、Python、uv、ffmpeg、ffprobeの前提を記載する。Windows PowerShellでは `npm.cmd` が必要な環境があることも補足する。依存関係の導入、コンテンツ検証、アセットビルド、Web起動、API起動、テスト、E2Eのコマンドを、実際にpackage scriptsと一致させる。

Content and Assets節では、22原型、22カード、`knowledge-arcana-vol-1`、front画像、パック共通back画像が存在することを記載し、「画像が未作成」という古い説明を削除または現在の残作業へ書き換える。元PNGとWeb配信用WebPの関係、asset catalog、manifest、content validationを説明する。

Architecture節では、抽選はTypeScript core、LLM鑑定はFastAPI、抽選はLLMへ委ねない、APIなしでも静的鑑定が動く、コンテンツはJSON Schemaで管理する、という境界を図または短い文章で示す。

Status and Roadmap節では、完了済み、実装中、次段階を明確に分ける。66枚、3枚引き、認証、PostgreSQL、課金を完成済みのように書かない。

README更新は最後に一度だけ行うのではなく、Milestone 1で開発コマンドの仮記載を追加し、Milestone 2でアセット記述を更新し、Milestone 7でAPI記述を更新し、Milestone 10で全コマンドを実行して最終整合させる。READMEに記載したコマンドはCIまたはドキュメントテストで可能な範囲を検証する。

このMilestoneの完了条件は、新規参加者がREADMEだけを読んで依存関係を導入し、コンテンツ検証、アセット生成、Web起動、API起動、テストを実行でき、記述された機能と実際の画面が一致することである。

### Milestone 10: テスト、CI、MVP受け入れを完了する

TypeScriptはVitestとReact Testing Libraryを使う。抽選、乱数、asset resolver、static interpretation、reducer、repository adapterを単体テストする。PythonはpytestとFastAPI test clientを使い、health、入力検証、content解決、Mock provider、fallbackをテストする。

Playwrightを `apps/sites-lite/e2e` またはルート `e2e` に置き、Chromiumを最低対象とする。viewportをスマートフォン縦画面に設定したシナリオを含める。E2Eでは相談入力、1枚引き、裏面表示、反転、正逆、静的鑑定、履歴保存、再読み込み、API Mock鑑定、API停止時fallbackを確認する。アニメーション時間をテスト時だけ短縮できる設定を用意し、固定sleepへ依存しない。

GitHub Actionsでは、Node依存導入、Python依存導入、content validation、asset metadata validation、TypeScript lint/typecheck/test/build、Python lint/typecheck/test、Playwrightを実行する。画像変換がCIで重い場合でも、asset catalogの参照、hash、寸法、存在確認は必須とし、変換自体を別jobへ分ける判断をDecision Logへ記録する。

このMilestoneの完了条件は、CIが緑になり、ローカルの受け入れ手順で1枚引きから履歴復元とAPI fallbackまで観察でき、READMEの全主要コマンドが現行スクリプトと一致することである。

## Concrete Steps

以下のコマンドはリポジトリルートで実行する。実装者は各Milestone完了時に実際のscript名へこの節を更新し、存在しないコマンドを残してはならない。

最初に現状を確認する。

    git status --short
    node --version
    npm --version
    python --version
    uv --version
    ffmpeg -version
    ffprobe -version
    npm install
    npm run validate:content

期待する初期結果は、コンテンツ検証が成功し、未コミット変更が意図したものだけであることである。

Milestone 1完了後は次を実行する。

    npm run dev:web

別ターミナルで次を実行する。

    cd apps/api
    uv sync
    uv run fastapi dev src/infinity_arcana_api/main.py

さらに別ターミナルで確認する。

    curl http://127.0.0.1:8000/api/health

期待する応答は次である。

    {"status":"ok"}

カード裏面を含むアセットを生成する。

    npm run assets:build
    npm run validate:content

期待するファイルは次である。

    apps/sites-lite/public/assets/packs/knowledge-arcana-vol-1/card-back.webp

TypeScript側の検証を実行する。

    npm run lint:web
    npm run typecheck:web
    npm run test:core
    npm run test:web
    npm run build:web

Python側の検証を実行する。

    cd apps/api
    uv run ruff check .
    uv run ruff format --check .
    uv run pyright
    uv run pytest

OpenAPIクライアントを生成する場合は、ルートに固定scriptを追加し、次の形で実行できるようにする。

    npm run api:generate
    git diff --exit-code -- packages/api-client

E2Eを実行する。

    npm run test:e2e

全体検証用の集約scriptを追加し、最終的には次の1コマンドで主要検証が走るようにする。

    npm run check

成功時の短い期待結果は、content validation成功、TypeScriptの全test成功、Pythonの全test成功、Vite build成功、Playwright成功である。テスト件数は実装中に増えるため、この計画では固定数を宣言せず、0件成功を成功扱いしない。

## Validation and Acceptance

MVPの受け入れは、内部ファイルの存在ではなく利用者の行動として確認する。

最初にAPIを起動せず、Webだけを起動する。スマートフォン相当の幅でトップ画面を開く。相談文として「新しい制作を始める前に、今は何を整理するべきですか」と入力し、1枚引きを開始する。`knowledge-arcana-vol-1` の共通裏面が伏せた状態で山から中央へ移動することを確認する。公開操作後、カードがY軸方向へ反転し、逆位置の場合だけカード全体がZ軸方向へ180度回転していることを確認する。カード名称、位置、静的鑑定、次の一歩が表示されることを確認する。

同じseedを開発用入力またはテストfixtureで指定して2回引き、同じcardIdとorientationになることを確認する。カード配列のJSON順をテストfixture内で変更しても結果が同じであることを単体テストで確認する。

画面を再読み込みし、履歴一覧に先ほどの鑑定が残り、詳細画面で同じカード画像と鑑定文を表示できることを確認する。図鑑で該当カードの発見回数が増えていることを確認する。

次にFastAPIをMock providerで起動し、新しい鑑定を行う。抽選後にAPI由来の鑑定が表示されることを確認する。APIを停止して再度鑑定し、利用者へ生のnetwork errorを見せず、静的鑑定へfallbackすることを確認する。APIの成功失敗でcardIdとorientationが変わらないことを確認する。

Reduced MotionをOSまたはブラウザ開発ツールで有効にし、長い移動や反転待ちが省略されても、伏せたカード、公開されたカード、正逆、鑑定という意味上の段階が保たれることを確認する。

エクスポートしたJSONを保存し、開発用のDBクリア操作後にインポートする。履歴と図鑑が復元されることを確認する。壊れたJSONをインポートしても既存データが消えず、利用者に理解できるエラーが表示されることを確認する。

最後にREADMEを新しい環境の視点で上から実行する。READMEに存在しないscript、古いファイルパス、未実装機能の完成表現がないことを確認する。

## Idempotence and Recovery

npm install、uv sync、content validation、asset build、テスト、Vite build、OpenAPI生成は繰り返し実行して同じ結果になるようにする。アセットビルドは同じ入力から同じ画像内容を生成し、生成時刻だけで無意味な差分を発生させない方法を優先する。生成時刻が必要な場合は、内容変更時だけcatalogを書き換える。

アセット変換が途中で失敗した場合、元PNGを変更または削除しない。出力は一時ファイルへ生成し、検証後に最終パスへ置換する。壊れたWebPが既存の正常ファイルを上書きしないようにする。

IndexedDB migrationが失敗した場合、既存データを即時削除しない。migration前にexportできる導線を保ち、開発環境でのみ明示的なreset操作を提供する。本番UIで自動resetを行わない。

OpenAPI生成差分が不正な場合、生成ファイルだけを削除して手書き型へ逃げない。Pydanticモデルを修正し、再生成する。APIクライアントの変更はAPI側の契約変更と同じコミットまたはPRに含める。

LLM接続が利用不能でもWebの抽選、静的鑑定、履歴、図鑑は動作する。APIキーがないことを起動失敗にせず、LLM providerを無効化してMockまたはStatic fallbackで起動できるようにする。

## Artifacts and Notes

最終的な主なリポジトリ構成は次を目標とする。細部が変わった場合は実際の構成へこの節を更新する。

    Infinity_Arcana/
    ├── apps/
    │   ├── sites-lite/
    │   │   ├── public/assets/
    │   │   ├── src/features/reading/
    │   │   ├── src/storage/
    │   │   └── package.json
    │   └── api/
    │       ├── src/infinity_arcana_api/
    │       ├── tests/
    │       ├── pyproject.toml
    │       └── uv.lock
    ├── packages/
    │   ├── core/
    │   ├── api-client/
    │   ├── content/
    │   ├── schemas/
    │   └── test-vectors/
    ├── tools/
    │   ├── build-assets.mjs
    │   └── validate-content.mjs
    ├── .agent/react-python-sites-lite-mvp.md
    ├── package.json
    ├── PLANS.md
    └── README.md

カード表示のDOM責務は次のように分ける。

    CardOrientation: upright/reversedをrotateZで表す外側
      CardFlip: back/front公開をrotateYで表す内側
        CardBack
        CardFront

抽選と演出乱数の分離は次の関係を保つ。

    DrawRequest + DrawRandomSource -> DrawResult
    DrawResult + AnimationPreferences -> AnimationPlan

`AnimationPreferences` を変更しても `DrawResult` は変化してはならない。

## Interfaces and Dependencies

ルートNode workspaceではnpmを使う。新規依存は各workspaceへ置き、ルートへすべてを集めない。Reactアプリは React、React DOM、TypeScript、Vite、Vitest、React Testing Library、Dexieを使う。React Routerは履歴と図鑑の画面追加時に導入する。PlaywrightはE2E用にルートまたはWeb workspaceへ置く。

Pythonは3.12以降を前提とし、uvでロックする。通常依存は `fastapi`、`pydantic`、`pydantic-settings`、利用するLLM SDKとする。開発依存は `pytest`、`pytest-asyncio`、`httpx`、`ruff`、`pyright` とする。SQLAlchemy、Alembic、PostgreSQL driverはこのMVPでは追加しない。

`packages/core/src/random/random-source.ts` に次の意味を持つインターフェースを定義する。

    export interface RandomSource {
      readonly algorithmId: string;
      readonly algorithmVersion: number;
      readonly seed: string;
      nextUint32(): number;
      nextInt(maxExclusive: number): number;
    }

`packages/core/src/draw/draw-policy.ts` に次の意味を持つインターフェースを定義する。

    export interface DrawPolicy {
      readonly id: string;
      readonly version: number;
      draw(context: DrawContext, random: RandomSource): DrawResult;
    }

`packages/core/src/repositories/reading-repository.ts` に次の意味を持つインターフェースを定義する。

    export interface ReadingRepository {
      save(reading: ReadingRecord): Promise<void>;
      findById(id: string): Promise<ReadingRecord | null>;
      listRecent(limit: number): Promise<ReadingRecord[]>;
      delete(id: string): Promise<void>;
      exportAll(): Promise<ReadingExport>;
      importAll(data: ReadingExport, strategy: "overwrite" | "skip"): Promise<ImportSummary>;
    }

`apps/api/src/infinity_arcana_api/providers/base.py` に次の意味を持つProtocolを定義する。

    class InterpretationProvider(Protocol):
        async def interpret(
            self,
            request: ResolvedInterpretationRequest,
        ) -> InterpretationResult:
            ...

`apps/api/src/infinity_arcana_api/services/content_service.py` はcontent release ID、spread ID、card ID、contentVersionを解決し、未知または不一致を拒否する。`InterpretationService` は解決済みデータ以外をproviderへ渡さない。

FastAPIのPydanticモデルとTypeScript APIクライアントの間ではOpenAPIを契約とする。コンテンツJSONでは既存JSON Schemaを契約とする。抽選の言語間互換性では `packages/test-vectors` を契約とする。この3種類を1つの自動生成方式へ無理に統一しない。

## Revision Note

2026-07-22: ReactとPythonの技術選定、カード裏面の正式統合、1枚引きSites Lite、IndexedDB、FastAPI鑑定、LLM fallback、テスト、CI、README更新までを一つの実行計画に統合するため、このExecPlanを新規作成した。