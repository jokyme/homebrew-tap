# Deskset Homebrew Tap

Official [Homebrew](https://brew.sh) tap for [Deskset](https://github.com/jokyme/Deskset) — native desktop widgets for macOS that also run Rainmeter skins.

## Install

```bash
brew install --cask jokyme/tap/deskset
```

Or in a `Brewfile`:

```ruby
tap "jokyme/tap", trusted: true
cask "jokyme/tap/deskset"
```

## Upgrade

Deskset checks for updates automatically in the app (**Deskset ▸ Check for Updates…**). To force an upgrade through Homebrew instead:

```bash
brew upgrade --cask --greedy jokyme/tap/deskset
```

## Uninstall

Keep your skins and layouts in `~/Library/Application Support/Deskset`:

```bash
brew uninstall --cask deskset
```

Remove Deskset together with all skins, layouts, caches, logs, and preferences:

```bash
brew uninstall --cask --zap deskset
```

---

## 中文说明

[Deskset](https://github.com/jokyme/Deskset) 官方 Homebrew 软件源。

- **安装：** `brew install --cask jokyme/tap/deskset`
- **通过 Homebrew 强制升级：** `brew upgrade --cask --greedy jokyme/tap/deskset`（也可直接在应用内检查更新）
- **卸载（保留皮肤与布局）：** `brew uninstall --cask deskset`
- **彻底卸载（同时清除皮肤、布局、缓存与偏好设置）：** `brew uninstall --cask --zap deskset`
