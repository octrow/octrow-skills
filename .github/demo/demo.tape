# Re-record from the repo root: sh .github/demo/setup.sh && vhs .github/demo/demo.tape
Output .github/demo.gif
Require git
Set Shell bash
Set FontSize 15
Set Width 1180
Set Height 760
Set Padding 18
Set Theme "GitHub Dark"
Set TypingSpeed 40ms

Hide
Type "export PS1='$ ' LESS=-R P=$PWD/plugins/repo-ready/skills/repo-publish/scripts && cd /tmp/weather-cli && clear"
Enter
Show

Type "python3 $P/preflight.py . --private acme | grep -v '^- ok' | cat -s | less"
Sleep 400ms
Enter
Sleep 6s
Space
Sleep 6s
Type "q"
