try:
    from sip_bench.harbor_codex_bridge import patch_harbor_codex_auth_bridge
except ModuleNotFoundError:
    patch_harbor_codex_auth_bridge = None


if patch_harbor_codex_auth_bridge is not None:
    try:
        patch_harbor_codex_auth_bridge()
    except ModuleNotFoundError:
        pass
