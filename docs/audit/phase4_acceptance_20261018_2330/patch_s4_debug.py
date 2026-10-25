with open('docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace('    finally:\n        engine.dispose()', '    except Exception as e:\n        import traceback\n        print("[STAGE 4 ERROR]", traceback.format_exc())\n    finally:\n        engine.dispose()')
with open('docs/audit/phase4_acceptance_20261018_2330/run_stages_3_4.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('PATCHED_DEBUG_S4')
