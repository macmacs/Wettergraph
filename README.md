# Wettergraph

#### Free, no ads and open source!

[<img src="fastlane/metadata/en_fdroid.png" height="60" alt="Get it on F-Droid">](https://macmacs.github.io/Wettergraph/)
This app is a fork of AF Weather Widget. It is a compact graphical weather graph as a single row Android widget. The source code is made public domain as it may provide utility for others. Please respect the various APIs used by the app, and please modify the user agent if you are running a modified version of the app.

## F-Droid repository

Signed release builds are published to a self-hosted F-Droid repository on GitHub Pages:

* Landing page: <https://macmacs.github.io/Wettergraph/>
* Repo URL: `https://macmacs.github.io/Wettergraph/fdroid/repo`
* Signing fingerprint (SHA-256): `ACABB6F7BF481DB77CE009F761BD94C40E96FEB0DBFF28FFDF8747E6C1AF586B`

Pushing a `v*` tag runs `.github/workflows/fdroid.yml`, which builds a signed release
APK, regenerates the index with `fdroidserver` and pushes the result to the `gh-pages`
branch. The repository configuration lives in `fdroid/`.

The workflow needs these repository secrets:

| Secret | Purpose |
| --- | --- |
| `KEYSTORE_BASE64` | base64 of the release keystore (aliases `apk` and `repo`) |
| `KEYSTORE_PASSWORD` | keystore and key password |
| `WETTERGRAPH_USER_AGENT` | met.no user agent |
| `WETTERGRAPH_API_KEY` | met.no API key |
| `WETTERGRAPH_USER_GEONAMES` | GeoNames username |

## Building locally

Copy `key.properties.example` to `key.properties` and fill in your own API
credentials, or export `WETTERGRAPH_USER_AGENT`, `WETTERGRAPH_API_KEY` and `WETTERGRAPH_USER_GEONAMES`.

## Screenshots

The F-Droid listing and the landing page screenshots are captured automatically
from an Android emulator, no real device required. The widget renders
synthetic, curated weather data via a debug-only mock hook, so the shots are
deterministic and never depend on live API data.

Capture runs:

* In CI: the `screenshots` job of `.github/workflows/fdroid.yml` runs on every
  `v*` tag push (and on manual dispatch). The fresh PNGs feed the published
  F-Droid index and are committed back to `main`.
* Locally: `scripts/capture-screenshots.sh` boots the emulator, captures the
  five shots and writes them into
  `fastlane/metadata/android/en-US/images/phoneScreenshots/`.

One-time local setup (emulator + system image + Pixel 9 display profile,
1080x2424 @ 420 dpi):

```sh
yes | sdkmanager --licenses
sdkmanager "emulator" "system-images;android-35;google_apis;x86_64"
echo no | avdmanager create avd -n wettergraph_pixel9 \
  -k "system-images;android-35;google_apis;x86_64" -d pixel_6
sed -i 's/^hw.lcd.width.*/hw.lcd.width = 1080/; s/^hw.lcd.height.*/hw.lcd.height = 2424/; s/^hw.lcd.density.*/hw.lcd.density = 420/' \
  ~/.android/avd/wettergraph_pixel9.avd/config.ini
```

The emulator needs hardware acceleration (KVM). The mock hook lives in
`AfMockData.java` and only activates in debug builds when the
`global_mock_weather` SharedPreferences key is set; release builds are
unaffected.

## Acknowledgements

* The Norwegian Meteorological Institute for providing an [open weather data API](https://api.met.no/#english).
* The National Weather Service for providing an [open weather data API](https://graphical.weather.gov/xml/rest.php).
* The GeoNames database for providing their [timezone and geoname API](http://www.geonames.org/export/web-services.html).
* Thanks to [bharathp666 from DeviantArt](http://bharathp666.deviantart.com/) for the [application icon](http://bharathp666.deviantart.com/art/Android-Weather-Icons-180719113) (`app_icon.png`).

## License

* All code written as part of the app is licensed as [CC0 Universal](https://creativecommons.org/publicdomain/zero/1.0/). The only exceptions are `MultiKey.java` and `Pair.java` which are licensed under Apache 2.0 as specified in their headers.
* The weather icons are owned by The Norwegian Meteorological Institute and are as provided via their [weathericon API](https://api.met.no/weatherapi/weathericon/2.0/documentation).

## Information for use

* Any use of the provided software must respect the terms of each API used.
* [The user agent information must be changed if used in a modified application.](app/src/main/java/io/github/macmacs/af/AfUtils.java#L545)
* [The GeoNames username must be changed if used in a modified application.](app/src/main/java/io/github/macmacs/af/data/AfGeoNamesData.java#L63)
