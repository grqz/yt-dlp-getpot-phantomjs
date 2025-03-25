A yt-dlp GetPOT plugin that attempts to generate POT with the phantomjs Javascript Interpreter.

Current status: works with an HTTP server on the python side.

The core code is located in [pot_http.es5.js](<js/src/pot_http.es5.cjs>).

# Installing

Requires yt-dlp **`2024.09.27`** or above.

## Installing with PyPI
If yt-dlp is installed through `pip` or `pipx`, you can install the plugin with the following:

**pip/pipx**

```
pipx inject yt-dlp yt-dlp-getpot-jsi
```
or

```
python3 -m pip install -U yt-dlp-getpot-jsi
```

This will automatically install the [GetPOT plugin](<https://github.com/coletdjnz/yt-dlp-get-pot>) if haven't installed it yet.

**Manual**

1. Install `yt-dlp-get-pot`. See [*Installing*](<https://github.com/coletdjnz/yt-dlp-get-pot?tab=readme-ov-file#installing>).
1. Go to the [latest release](<https://github.com/grqz/yt-dlp-getpot-jsi/releases/latest>).
2. Find `yt-dlp-getpot-jsi.zip` and download it to one of the [yt-dlp plugin locations](<https://github.com/yt-dlp/yt-dlp#installing-plugins>)

    - User Plugins
        - `${XDG_CONFIG_HOME}/yt-dlp/plugins` (recommended on Linux/macOS)
        - `~/.yt-dlp/plugins/`
        - `${APPDATA}/yt-dlp/plugins/` (recommended on Windows)
    
    - System Plugins
       -  `/etc/yt-dlp/plugins/`
       -  `/etc/yt-dlp-plugins/`
    
    - Executable location
        - Binary: where `<root-dir>/yt-dlp.exe`, `<root-dir>/yt-dlp-plugins/`

For more locations and methods, see [installing yt-dlp plugins](<https://github.com/yt-dlp/yt-dlp#installing-plugins>)


If installed correctly, you should see the provider's version in `yt-dlp -v` output:

    [debug] [GetPOT] PO Token Providers: PhantomJS-XXX
