# Sets the tags and adds the screenshots of the Formables Atlas workshop item via the Steamworks flat API.
# Requires the Steam client running and logged in as the item owner.
import ctypes, os, sys, time

APP_ID = 3450310
ITEM_ID = 3815303367
TAGS = ["Economy", "1.4"]
BIN = r"E:\SteamLibrary\steamapps\common\Europa Universalis V\binaries"
K_SUBMIT_ITEM_UPDATE_RESULT = 3404  # k_iSteamUGCCallbacks + 4


class SteamParamStringArray(ctypes.Structure):
    _fields_ = [("strings", ctypes.POINTER(ctypes.c_char_p)), ("count", ctypes.c_int32)]


class SubmitItemUpdateResult(ctypes.Structure):
    _pack_ = 8
    _fields_ = [("result", ctypes.c_int32), ("needs_legal_agreement", ctypes.c_bool),
                ("published_file_id", ctypes.c_uint64)]


os.environ["SteamAppId"] = str(APP_ID)
os.environ["SteamGameId"] = str(APP_ID)
# steam_api64_o.dll is Valve's original library; steam_api64.dll in this folder is a wrapper around it.
name = "steam_api64_o.dll" if os.path.exists(os.path.join(BIN, "steam_api64_o.dll")) else "steam_api64.dll"
api = ctypes.CDLL(os.path.join(BIN, name))

api.SteamAPI_Init.restype = ctypes.c_bool
if not api.SteamAPI_Init():
    sys.exit("SteamAPI_Init failed: is Steam running and logged in?")

def accessor(prefix, versions):
    for v in versions:
        try:
            f = getattr(api, f"{prefix}_v{v:03d}")
        except AttributeError:
            continue
        f.restype = ctypes.c_void_p
        print(f"using {prefix}_v{v:03d}")
        return ctypes.c_void_p(f())
    sys.exit(f"no {prefix} accessor found")


ugc = accessor("SteamAPI_SteamUGC", range(25, 9, -1))
utils = accessor("SteamAPI_SteamUtils", range(12, 7, -1))

api.SteamAPI_ISteamUGC_StartItemUpdate.restype = ctypes.c_uint64
api.SteamAPI_ISteamUGC_StartItemUpdate.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint64]
api.SteamAPI_ISteamUGC_SetItemTags.restype = ctypes.c_bool
api.SteamAPI_ISteamUGC_SetItemTags.argtypes = [ctypes.c_void_p, ctypes.c_uint64,
                                               ctypes.POINTER(SteamParamStringArray), ctypes.c_bool]
api.SteamAPI_ISteamUGC_AddItemPreviewFile.restype = ctypes.c_bool
api.SteamAPI_ISteamUGC_AddItemPreviewFile.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_char_p, ctypes.c_int]
api.SteamAPI_ISteamUGC_SubmitItemUpdate.restype = ctypes.c_uint64
api.SteamAPI_ISteamUGC_SubmitItemUpdate.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_char_p]
api.SteamAPI_ISteamUtils_IsAPICallCompleted.restype = ctypes.c_bool
api.SteamAPI_ISteamUtils_IsAPICallCompleted.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_bool)]
api.SteamAPI_ISteamUtils_GetAPICallResult.restype = ctypes.c_bool
api.SteamAPI_ISteamUtils_GetAPICallResult.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_void_p,
                                                      ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_bool)]

handle = api.SteamAPI_ISteamUGC_StartItemUpdate(ugc, APP_ID, ITEM_ID)
arr = (ctypes.c_char_p * len(TAGS))(*[t.encode() for t in TAGS])
tags = SteamParamStringArray(arr, len(TAGS))
if not api.SteamAPI_ISteamUGC_SetItemTags(ugc, handle, ctypes.byref(tags), False):
    sys.exit("SetItemTags rejected the tags")
SHOTS = [r"C:/1212/export_ban/shots/shot%d.jpg" % n for n in range(1, 7)]
for shot in SHOTS:  # k_EItemPreviewType_Image = 0
    if not api.SteamAPI_ISteamUGC_AddItemPreviewFile(ugc, handle, shot.encode(), 0):
        sys.exit("AddItemPreviewFile rejected " + shot)
call = api.SteamAPI_ISteamUGC_SubmitItemUpdate(ugc, handle, b"Tags and screenshots")

failed = ctypes.c_bool(False)
deadline = time.time() + 120
while not api.SteamAPI_ISteamUtils_IsAPICallCompleted(utils, call, ctypes.byref(failed)):
    api.SteamAPI_RunCallbacks()
    if time.time() > deadline:
        sys.exit("Timed out waiting for Steam")
    time.sleep(0.2)

res = SubmitItemUpdateResult()
ok = api.SteamAPI_ISteamUtils_GetAPICallResult(utils, call, ctypes.byref(res), ctypes.sizeof(res),
                                               K_SUBMIT_ITEM_UPDATE_RESULT, ctypes.byref(failed))
print(f"call ok={ok} io_failed={failed.value} EResult={res.result} item={res.published_file_id} "
      f"needs_legal_agreement={res.needs_legal_agreement}")
api.SteamAPI_Shutdown()
sys.exit(0 if ok and res.result == 1 else 1)
