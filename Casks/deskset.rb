cask "deskset" do
  arch arm: "arm64", intel: "x86_64"

  version "1.1.0"
  sha256 arm:   "a3cb838951e6f7822cef68defb0737ce4d9033a84ffaf4f62a00520217cfd7e2",
         intel: "05e9a492f7d40249966aa96e3a1a2e73ac466ec7958af3d95e0f1896154504d8"

  url "https://github.com/jokyme/Deskset/releases/download/v#{version}/Deskset-#{version}-#{arch}.dmg"
  name "Deskset"
  desc "Desktop widgets that also run Rainmeter skins"
  homepage "https://www.ideskset.com/"

  livecheck do
    url :url
    strategy :github_latest
  end

  auto_updates true
  depends_on macos: :ventura

  app "Deskset.app"

  uninstall quit: "app.deskset.Deskset"

  zap trash: [
    "~/Library/Application Support/Deskset",
    "~/Library/Caches/app.deskset.Deskset",
    "~/Library/Caches/Deskset",
    "~/Library/Logs/Deskset",
    "~/Library/Preferences/app.deskset.Deskset.plist",
  ]
end
