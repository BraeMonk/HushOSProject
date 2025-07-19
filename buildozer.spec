name: Build HushOS APK
on:
  push:
    branches:
      - main
  workflow_dispatch:
jobs:
  build-android:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Free up disk space
        run: |
          sudo rm -rf /usr/share/dotnet
          sudo rm -rf /opt/ghc
          sudo rm -rf "/usr/local/share/boost"
          sudo rm -rf "$AGENT_TOOLSDIRECTORY"
          sudo apt-get autoremove -y
          sudo apt-get autoclean -y
          df -h
      
      - name: Build with Buildozer
        uses: ArtemSBulgakov/buildozer-action@v1
        id: buildozer
        with:
          buildozer_version: "1.5.0"
          command: |
            # The buildozer.spec already has the correct versions, so we don't need to set them again
            # Just run the build with verbose output
            buildozer -v android debug
        env:
          # Memory settings for Gradle and Java processes
          GRADLE_OPTS: -Xmx4g -XX:MaxMetaspaceSize=512m -XX:+UseG1GC -XX:+HeapDumpOnOutOfMemoryError
          JAVA_OPTS: -Xmx3g -XX:MaxMetaspaceSize=512m
          _JAVA_OPTIONS: -Xmx3g -XX:MaxMetaspaceSize=512m
          # Reduce parallelism to save memory
          GRADLE_MAX_WORKERS: 2
      
      - name: Upload APK artifact
        uses: actions/upload-artifact@v4
        with:
          name: hush-os-apk
          path: ${{ steps.buildozer.outputs.apk_path }}
          if-no-files-found: error
