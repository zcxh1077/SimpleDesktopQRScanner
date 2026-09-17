# SimpleDesktopQRScanner

画面に表示されている QR コードを読み取る **Windows 専用**のデスクトップアプリです。
ウィンドウの枠の中が透けているので、読み取りたい QR コードを枠内に収めるだけで結果が表示されます。

## 使い方

1. [Releases](https://github.com/zcxh1077/SimpleDesktopQRScanner/releases) から `SimpleDesktopQRScanner.exe` をダウンロードして起動します（Python は不要です）。
2. ウィンドウを QR コードの上に移動し、赤い枠の中に QR コードが収まるようにします。ウィンドウの大きさは自由に変えられます。
3. 下のバーに読み取り結果が表示されます。
   - **URL**（`http://` / `https://`）: リンクをクリックするとブラウザで開きます。
   - **テキスト**: 「コピー」ボタンでクリップボードにコピーします。

- 複数の QR コードが枠内にある場合は、すべて表示されます。
- QR コードが枠から外れても、最後の結果は表示されたままです。

> 初回起動時に Windows SmartScreen の警告が出た場合は、「詳細情報」→「実行」を選んでください（署名なしの exe のため）。
> ダウンロードしたファイルは、Release に記載の SHA256 と `Get-FileHash SimpleDesktopQRScanner.exe` の結果が一致するか確認できます。

## 開発

必要なもの: Windows、Python 3.13

```powershell
pip install -r requirements.txt
python qrscan.py              # 起動
python qrscan.py --selftest   # QR の生成→読み取りの自己テスト
```

### exe のビルド

```powershell
pip install pyinstaller
pyinstaller --noconfirm --onefile --noconsole --noupx --name SimpleDesktopQRScanner qrscan.py
```

`dist\SimpleDesktopQRScanner.exe` が生成されます。
（UPX 圧縮はウイルス対策ソフトの誤検知を招きやすいため無効にしています）

## 仕組み

- **UI**: tkinter。常に最前面に表示します。
- **透過部分**: `SetWindowRgn` でウィンドウに実際の穴を開けています。
  tkinter の `-transparentcolor` を使うとウィンドウ全体がクリックを透過してしまい、ボタンが押せなかったためです。
- **画面キャプチャ**: GDI の `BitBlt` で枠内だけを取得します（約 8ms）。
  Pillow の `ImageGrab` はデスクトップ全体を取得するため遅く（約 80ms）、動作がカクついていました。
- **デコード**: [zxing-cpp](https://github.com/zxing-cpp/zxing-cpp)。0.3 秒ごとに読み取ります。
- 高 DPI 環境でも座標がずれないよう、Per-Monitor DPI Aware で動作します。

## ライセンス

[MIT](LICENSE)

---

*作成日時: 2026年9月17日 17:13:46 JST*
