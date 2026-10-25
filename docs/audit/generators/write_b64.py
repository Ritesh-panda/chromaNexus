import sys, base64

if len(sys.argv) < 2:
    print('Usage: python write_b64.py <target_file> [base64_string]')
    sys.exit(1)

target = sys.argv[1]
if len(sys.argv) >= 3:
    b64_str = sys.argv[2]
else:
    b64_str = sys.stdin.read()

with open(target, 'wb') as f:
    f.write(base64.b64decode(b64_str.strip()))
print(f'Successfully wrote {target}')
