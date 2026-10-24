# Delegate to the comprehensive offline validator so both entry points agree.
python (Join-Path $PSScriptRoot "generate_and_validate.py")
exit $LASTEXITCODE
