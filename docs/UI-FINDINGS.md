# Gameplay UI findings

Cumulative record of captured play sessions. Updated by `python3 tools/ui_audit.py collect`; previous sessions remain in the archive.

Updated 2026-10-21 22:13 UTC. **1 session, 2,884 distinct widget IDs.**

268 edge-HUD candidates, 3 marker widget/owner families without latest recorded coverage (12 historical), and 1 interaction-hint context with visible keyboard presentation.

These are observations for review. Edge bounds do not prove headset clipping; screen components do not prove faulty tracking. Missing from a later session does not mean fixed. Arbitrary literal FText strings are not inspected.

## Sessions

| Session | Engine seconds | IDs | Errors/parse notes | End |
| --- | ---: | ---: | ---: | --- |
| robot1-x/ui-audit-000001 | 825.5 | 2884 | 0 | stopped |

## HUD near the edges

Bounds and widget paths are in the dictionary below. Diagnostic margins are configurable in `data/tuning.ini`; capture does not reposition HUD.

| HUD root | Candidate IDs |
| --- | ---: |
| WidgetBlueprintGeneratedClass /Game/Interfaces/Boss/UI_Lifebar_Boss.UI_Lifebar_Boss_C | 1 |
| WidgetBlueprintGeneratedClass /Game/Interfaces/Equipment/UI_Equipment_Tweak_Hero.UI_Equipment_Tweak_Hero_C | 4 |
| WidgetBlueprintGeneratedClass /Game/Interfaces/Leaderboard/UI_Leaderboard.UI_Leaderboard_C | 4 |
| WidgetBlueprintGeneratedClass /Game/Interfaces/MainMenu/UI_TitleScreen.UI_TitleScreen_C | 26 |
| WidgetBlueprintGeneratedClass /Game/Interfaces/Map/UI_Map.UI_Map_C | 21 |
| WidgetBlueprintGeneratedClass /Game/Interfaces/Map/UI_MissionStart.UI_MissionStart_C | 1 |
| WidgetBlueprintGeneratedClass /Game/Interfaces/Preparation/UI_StartMission.UI_StartMission_C | 50 |
| WidgetBlueprintGeneratedClass /Game/Interfaces/UI_BuildId.UI_BuildId_C | 1 |
| WidgetBlueprintGeneratedClass /Game/Interfaces/UI_LoadingScreen.UI_LoadingScreen_C | 19 |
| WidgetBlueprintGeneratedClass /Game/Interfaces/UI_Player.UI_Player_C | 65 |
| WidgetBlueprintGeneratedClass /Game/Interfaces/UI_PlayerLobby.UI_PlayerLobby_C | 76 |

## World-marker families

Historical unhandled observations are retained even if coverage is observed later.

| Widget class | World owner class | Latest coverage |
| --- | --- | --- |
| WidgetBlueprintGeneratedClass /Game/Interfaces/Pings/UI_PingObjective.UI_PingObjective_C | BlueprintGeneratedClass /Game/Gamework/ObjectivePing/BP_ObjectivePing_Arrival.BP_ObjectivePing_Arrival_C | correction observed |
| WidgetBlueprintGeneratedClass /Game/Interfaces/Pings/UI_PingObjective.UI_PingObjective_C | BlueprintGeneratedClass /Game/Gamework/ObjectivePing/BP_ObjectivePing_Boss.BP_ObjectivePing_Boss_C | correction observed |
| WidgetBlueprintGeneratedClass /Game/Interfaces/Pings/UI_PingObjective.UI_PingObjective_C | BlueprintGeneratedClass /Game/Gamework/ObjectivePing/BP_ObjectivePing_Extraction.BP_ObjectivePing_Extraction_C | correction observed |
| WidgetBlueprintGeneratedClass /Game/Interfaces/Pings/UI_PingObjective.UI_PingObjective_C | BlueprintGeneratedClass /Game/Gamework/ObjectivePing/BP_ObjectivePing_Lighthouse.BP_ObjectivePing_Lighthouse_C | correction observed |
| WidgetBlueprintGeneratedClass /Game/Interfaces/Pings/UI_PingObjective.UI_PingObjective_C | BlueprintGeneratedClass /Game/Gamework/ObjectivePing/BP_ObjectivePing_Main.BP_ObjectivePing_Main_C | correction observed |
| WidgetBlueprintGeneratedClass /Game/Interfaces/Pings/UI_PingObjective.UI_PingObjective_C | BlueprintGeneratedClass /Game/Gamework/ObjectivePing/BP_ObjectivePing_NPC.BP_ObjectivePing_NPC_C | correction observed |
| WidgetBlueprintGeneratedClass /Game/Interfaces/Pings/UI_PingObjective.UI_PingObjective_C | BlueprintGeneratedClass /Game/Gamework/ObjectivePing/BP_ObjectivePing_SideObjective.BP_ObjectivePing_SideObjective_C | correction observed |
| WidgetBlueprintGeneratedClass /Game/Interfaces/UI_Guide.UI_Guide_C | BlueprintGeneratedClass /Game/GPE/Tools/BP_TextGuide.BP_TextGuide_C | correction observed |
| WidgetBlueprintGeneratedClass /Game/Interfaces/UI_Lifebar.UI_Lifebar_C | BlueprintGeneratedClass /Game/Enemies/BP_Enemy_Cryptic_Nuker.BP_Enemy_Cryptic_Nuker_C | none recorded |
| WidgetBlueprintGeneratedClass /Game/Interfaces/UI_Lifebar.UI_Lifebar_C | BlueprintGeneratedClass /Game/GPE/BP_RadioactiveBarrel.BP_RadioactiveBarrel_C | none recorded |
| WidgetBlueprintGeneratedClass /Game/Interfaces/UI_Lifebar.UI_Lifebar_C | BlueprintGeneratedClass /Game/Objectives/Assets/Alkemisto/BP_GasBomb_BossSpawner.BP_GasBomb_BossSpawner_C | none recorded |
| WidgetBlueprintGeneratedClass /Game/Interfaces/UI_WorldIcon.UI_WorldIcon_C | BlueprintGeneratedClass /Game/Lobby/BP_WorldIcon.BP_WorldIcon_C | correction observed |

## Interaction hints that displayed keyboard input

| ID | Widget path | Modes observed | Sessions |
| --- | --- | --- | --- |
| w-fd7113bb1e4f | `UI_Interact_C/InvalidationBox_0/VerticalBox_56/Overlay_101/HorizontalBox_69/UI_Key` | +gamepad, keyboard | 1 |

## Candidate dictionary

IDs are stable SHA-256 abbreviations of the full class/path ID stored in `catalog.json` and the CSV reports. Coordinates are fractions of viewport width/height from the latest visible observation. Counts deduplicate session checkpoints. Each raw session keeps its original measurements.

<details>
<summary>283 candidate widget IDs</summary>

| ID | Type | Widget path | Bounds (left, top → right, bottom) | Sessions | Latest coverage |
| --- | --- | --- | --- | ---: | --- |
| w-7b53c89f740c | unhandled_screen_marker | `UI_Guide_C/InvalidationBox_0/Overlay_0/Border_0` | 1.123, 0.289 → 1.195, 0.309 | 1 | mission guide:source |
| w-f17634b8b6cd | unhandled_screen_marker | `UI_Lifebar_C/Border_0` | 0.475, 0.451 → 0.544, 0.481 | 1 | none recorded |
| w-c3bf5a7a0778 | unhandled_screen_marker | `UI_WorldIcon_C/Border_0` | 0.348, 0.373 → 0.398, 0.430 | 1 | UI_WorldIcon_C:proxy, UI_WorldIcon_C:source |
| w-e9e68bd63117 | unhandled_screen_marker | `UI_Guide_C/InvalidationBox_0/Overlay_0/Image_Aura` | 1.096, 0.282 → 1.221, 0.336 | 1 | mission guide:source |
| w-f9cd64a35c23 | edge_hud | `UI_Lifebar_Boss_C/CanvasPanel_63/TextBackground` | 0.370, 0.142 → 0.630, 0.271 | 1 | none recorded |
| w-cea97c99e739 | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox/UI_Map_Task_Bounty_2/HorizontalBox_35/Image_Icon` | 0.082, 0.273 → 0.108, 0.319 | 1 | none recorded |
| w-014e1595686c | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox/UI_Map_Task_Extract_1/HorizontalBox_35/Image_Icon` | 0.082, 0.334 → 0.108, 0.380 | 1 | none recorded |
| w-aa0d737220ac | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox/UI_Map_Task_Reveal_1/HorizontalBox_35/Image_Icon` | 0.082, 0.212 → 0.108, 0.258 | 1 | none recorded |
| w-40a56907f9b3 | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_1/HorizontalBox_35/Image_Icon` | 0.479, 0.952 → 0.499, 0.988 | 1 | none recorded |
| w-b93b4216ed6f | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_2/HorizontalBox_35/Image_Icon` | 0.366, 0.956 → 0.382, 0.984 | 1 | none recorded |
| w-a5193f63602d | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_3/HorizontalBox_35/Image_Icon` | 0.309, 0.956 → 0.325, 0.984 | 1 | none recorded |
| w-de55d70e681c | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_4/HorizontalBox_35/Image_Icon` | 0.433, 0.956 → 0.449, 0.984 | 1 | none recorded |
| w-a53c39d31dd4 | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_5/HorizontalBox_35/Image_Icon` | 0.639, 0.956 → 0.655, 0.984 | 1 | none recorded |
| w-89bff6a9ac53 | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_6/HorizontalBox_35/Image_Icon` | 0.568, 0.956 → 0.583, 0.984 | 1 | none recorded |
| w-79d29a4bfe27 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/Crosshair_Top` | 0.433, 0.381 → 0.567, 0.619 | 1 | none recorded |
| w-3e080db22a93 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Image_GamepadIcon` | 0.046, 0.832 → 0.062, 0.859 | 1 | none recorded |
| w-0f9baca42b35 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/HorizontalBox_Holder/SpellIcon` | 0.026, 0.832 → 0.042, 0.859 | 1 | none recorded |
| w-2776cb0db921 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Image_GamepadIcon` | 0.053, 0.868 → 0.069, 0.895 | 1 | none recorded |
| w-7bace8f246ad | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/HorizontalBox_Holder/SpellIcon` | 0.033, 0.868 → 0.049, 0.895 | 1 | none recorded |
| w-fc3480819f8d | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Image_GamepadIcon` | 0.084, 0.904 → 0.100, 0.931 | 1 | none recorded |
| w-81c3103f3fc5 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/HorizontalBox_Holder/SpellIcon` | 0.041, 0.903 → 0.057, 0.930 | 1 | none recorded |
| w-df95a7df02b1 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox/Image` | 0.876, 0.062 → 0.890, 0.085 | 1 | none recorded |
| w-af9c299dcc6a | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_1/Image_1` | 0.658, 0.061 → 0.672, 0.085 | 1 | none recorded |
| w-f3b351c33ea2 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_2/Image_2` | 0.812, 0.061 → 0.826, 0.085 | 1 | none recorded |
| w-7389e4f1969a | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_3/Image_3` | 0.738, 0.061 → 0.752, 0.085 | 1 | none recorded |
| w-2a663db2929a | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_6/Image_6` | 0.962, 0.062 → 0.977, 0.085 | 1 | none recorded |
| w-a3920247b8bc | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes/Icon_Emote` | 0.955, 0.784 → 0.971, 0.811 | 1 | none recorded |
| w-ae7555235db3 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes/UI_Key_Emotes/HorizontalBox_2/Image_GamepadIcon` | 0.936, 0.781 → 0.950, 0.805 | 1 | none recorded |
| w-3a83ed0eaddc | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/HB_Battlecry_Gamepad/UI_Key_BattleCry/HorizontalBox_2/Image_GamepadIcon` | 0.905, 0.812 → 0.919, 0.836 | 1 | none recorded |
| w-a5615d6c21c0 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/HB_Battlecry_Gamepad/UI_Key_BattleCry_2/HorizontalBox_2/Image_GamepadIcon` | 0.936, 0.812 → 0.950, 0.836 | 1 | none recorded |
| w-7764d5845298 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/Icon_Emote_2` | 0.956, 0.814 → 0.972, 0.841 | 1 | none recorded |
| w-f3c903117c3f | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Melee/IconMelee` | 0.956, 0.845 → 0.972, 0.872 | 1 | none recorded |
| w-3d98c3416e0a | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Melee/UI_Key_Melee/HorizontalBox_2/Image_GamepadIcon` | 0.937, 0.842 → 0.951, 0.866 | 1 | none recorded |
| w-e7a5086746d0 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Quests/IconQuests` | 0.956, 0.875 → 0.972, 0.902 | 1 | none recorded |
| w-0b0f415d550a | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Quests/UI_key_Quest/HorizontalBox_2/Image_GamepadIcon` | 0.937, 0.872 → 0.951, 0.896 | 1 | none recorded |
| w-4cec78d065e0 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/HB_Ammo/Image_CurrentWeapon` | 0.962, 0.903 → 0.978, 0.930 | 1 | none recorded |
| w-91a040fc9dfa | edge_hud | `UI_Player_C/CanvasPanel_39/Crosshair_Top` | 0.412, 0.178 → 0.546, 0.331 | 1 | none recorded |
| w-334746a28eae | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/Border_110/HorizontalBox_0/Image_105` | 0.314, 0.914 → 0.314, 0.914 | 1 | none recorded |
| w-6156a4507bbd | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Moneys/HorizontalBox_463/Overlay/Image_Uranium` | 0.949, 0.069 → 0.963, 0.092 | 1 | none recorded |
| w-e6e2eb2f06cf | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Moneys/HorizontalBox_463/Overlay_0/Image_Golds` | 0.871, 0.067 → 0.887, 0.094 | 1 | none recorded |
| w-c76dc8bc297a | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Moneys/HorizontalBox_463/Overlay_2/Image_GlowEnemyMoney` | 0.848, -0.045 → 0.993, 0.201 | 1 | none recorded |
| w-802fc6f5f927 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Moneys/HorizontalBox_463/Overlay_2/Image_Souls` | 0.911, 0.067 → 0.927, 0.094 | 1 | none recorded |
| w-810f8648c383 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Image_GamepadIcon` | 0.052, 0.832 → 0.068, 0.859 | 1 | none recorded |
| w-91c77816187a | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/HorizontalBox_Holder/SpellIcon` | 0.027, 0.831 → 0.042, 0.858 | 1 | none recorded |
| w-00e0c13eaaff | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Image_GamepadIcon` | 0.059, 0.868 → 0.075, 0.895 | 1 | none recorded |
| w-90673947e3a7 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/HorizontalBox_Holder/SpellIcon` | 0.034, 0.866 → 0.050, 0.893 | 1 | none recorded |
| w-66f49dc9efda | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Image_GamepadIcon` | 0.088, 0.902 → 0.104, 0.929 | 1 | none recorded |
| w-a28cd219e797 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/HorizontalBox_Holder/SpellIcon` | 0.041, 0.902 → 0.057, 0.929 | 1 | none recorded |
| w-7e3cd352b6e6 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/Image_Glow` | 0.040, 0.847 → 0.127, 0.994 | 1 | none recorded |
| w-9980d50418d7 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/HB_Ammo/Image_CurrentWeapon` | 0.962, 0.899 → 0.978, 0.926 | 1 | none recorded |
| w-0fcabf0ae6c5 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_Grenades/IconGrenade` | 0.960, 0.868 → 0.976, 0.895 | 1 | none recorded |
| w-a786d8b92ec8 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_Grenades/UI_Key_2/HorizontalBox_2/Image_GamepadIcon` | 0.939, 0.865 → 0.955, 0.892 | 1 | none recorded |
| w-4c4b07776e32 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_Map/IconGrenade_1` | 0.961, 0.838 → 0.977, 0.865 | 1 | none recorded |
| w-02eb3fbb9262 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_Map/UI_Key/HorizontalBox_2/Image_GamepadIcon` | 0.939, 0.835 → 0.955, 0.862 | 1 | none recorded |
| w-1abafb6461da | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_MapAndHorse/IconHorse` | 0.961, 0.808 → 0.977, 0.835 | 1 | none recorded |
| w-383b934c4eaf | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_MapAndHorse/UI_Key_1/HorizontalBox_2/Image_GamepadIcon` | 0.940, 0.805 → 0.956, 0.832 | 1 | none recorded |
| w-da8fd89b10d6 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_RegionImage_/Image_Region` | 0.927, 0.385 → 1.207, 0.884 | 1 | none recorded |
| w-ccdbae388521 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_RegionImage_Area41/Image_Region` | 0.154, 0.478 → 0.474, 1.047 | 1 | none recorded |
| w-f4e31f250d06 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_RegionImage_Desert/Image_Region` | 0.355, 0.356 → 0.675, 0.924 | 1 | none recorded |
| w-6ae930269e84 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_RegionImage_FarFarNorth/Image_Region` | 0.533, -0.124 → 0.853, 0.444 | 1 | none recorded |
| w-4a3f62f15da1 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_RegionImage_FarWest/Image_Region` | 0.305, 0.144 → 0.625, 0.713 | 1 | none recorded |
| w-4154b3264026 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_RegionImage_Jungle/Image_Region` | 0.824, 0.180 → 1.105, 0.680 | 1 | none recorded |
| w-735069271353 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_RegionImage_Woodlands/Image_Region` | 0.530, 0.378 → 0.890, 1.017 | 1 | none recorded |
| w-257336ca6203 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_Region_Brimtstone/VerticalBox_0/Button_Hover/VerticalBox_1/Image_Lock` | 1.060, 0.697 → 1.079, 0.730 | 1 | none recorded |
| w-f61b11394ffe | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_Region_FarFarNorth/VerticalBox_0/Button_Hover/VerticalBox_1/Image_Lock` | 0.694, 0.088 → 0.712, 0.121 | 1 | none recorded |
| w-f64497d44968 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_Region_Jungle/VerticalBox_0/Button_Hover/VerticalBox_1/Image_Lock` | 0.931, 0.343 → 0.950, 0.377 | 1 | none recorded |
| w-dd30bf0d4978 | edge_hud | `UI_StartMission_C/CanvasPanel_0/HorizontalBox_4/Image_118` | 0.846, 0.087 → 0.861, 0.113 | 1 | none recorded |
| w-4c5d83a95c17 | edge_hud | `UI_StartMission_C/CanvasPanel_0/UI_Equipment_GoBack/Button_GoBack/HorizontalBox_0/Image_47` | 0.012, 0.016 → 0.023, 0.053 | 1 | none recorded |
| w-8cae19443844 | edge_hud | `UI_StartMission_C/CanvasPanel_0/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox/Image` | 0.885, 0.020 → 0.899, 0.046 | 1 | none recorded |
| w-2c4596e78290 | edge_hud | `UI_StartMission_C/CanvasPanel_0/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_1/Image_1` | 0.660, 0.020 → 0.674, 0.046 | 1 | none recorded |
| w-49f7a4a783d4 | edge_hud | `UI_StartMission_C/CanvasPanel_0/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_2/Image_2` | 0.818, 0.020 → 0.833, 0.046 | 1 | none recorded |
| w-42ca1ffed31c | edge_hud | `UI_StartMission_C/CanvasPanel_0/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_3/Image_3` | 0.743, 0.020 → 0.757, 0.046 | 1 | none recorded |
| w-15dbccdcf886 | edge_hud | `UI_StartMission_C/CanvasPanel_0/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_6/Image_6` | 0.973, 0.020 → 0.988, 0.046 | 1 | none recorded |
| w-c2f6d1c894aa | edge_hud | `UI_StartMission_C/CanvasPanel_0/VB_ContractHolder/UI_Contract/Overlay_Main/Image_SelectedIcon` | 0.002, 0.178 → 0.244, 0.642 | 1 | none recorded |
| w-391aac8c6210 | edge_hud | `UI_StartMission_C/CanvasPanel_0/VerticalBox_0/UI_Template_GenerateContracts/Button_Tab/Border_Color/HorizontalBox_Content/Image_Icon` | 0.840, 0.877 → 0.855, 0.905 | 1 | none recorded |
| w-14f5b0077496 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_116/SizeBox_0/Image_92` | -0.053, -0.011 → 0.447, 0.489 | 1 | none recorded |
| w-4709eafd7a73 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_116/UI_Template_BroweSessions/Button_Tab/Overlay_0/Border_Color/Border_Padding/HorizontalBox_0/Image_Icon` | 0.093, 0.474 → 0.114, 0.511 | 1 | none recorded |
| w-994dd156d71d | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_116/UI_Template_CreateSession/Button_Tab/Overlay_0/Border_Color/Border_Padding/HorizontalBox_0/Image_Icon` | 0.093, 0.396 → 0.114, 0.433 | 1 | none recorded |
| w-b4ff3cb59687 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_116/UI_Template_Credits/Button_Tab/Overlay_0/Border_Color/Border_Padding/HorizontalBox_0/Image_Icon` | 0.093, 0.708 → 0.114, 0.745 | 1 | none recorded |
| w-03aa466e5a4b | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_116/UI_Template_Options/Button_Tab/Overlay_0/Border_Color/Border_Padding/HorizontalBox_0/Image_Icon` | 0.093, 0.630 → 0.114, 0.667 | 1 | none recorded |
| w-0091aa3e35b6 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_116/UI_Template_Quit/Button_Tab/Overlay_0/Border_Color/Border_Padding/HorizontalBox_0/Image_Icon` | 0.093, 0.786 → 0.114, 0.823 | 1 | none recorded |
| w-2e34955d5839 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_116/UI_Template_Tutorial/Button_Tab/Overlay_0/Border_Color/Border_Padding/HorizontalBox_0/Image_Icon` | 0.093, 0.552 → 0.114, 0.589 | 1 | none recorded |
| w-3b0105cf9af3 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/VerticalBox_0/UI_Template_PatchNote/Button_Tab/Overlay_0/Border_Color/Border_Padding/HorizontalBox_0/Image_Icon` | 0.741, 0.838 → 0.765, 0.880 | 1 | none recorded |
| w-4559108fb164 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/UI_Equipment_GoBack/Button_GoBack/HorizontalBox_0/Image_47` | 0.012, 0.016 → 0.023, 0.053 | 1 | none recorded |
| w-18d4a0d5e8b6 | unhandled_screen_marker | `UI_WorldIcon_C/Border_0/Image_Icon` | 0.336, 0.408 → 0.353, 0.427 | 1 | UI_WorldIcon_C:proxy, UI_WorldIcon_C:source |
| w-67d655e6f524 | unhandled_screen_marker | `UI_Guide_C/InvalidationBox_0` | 0.172, 0.359 → 0.244, 0.378 | 1 | mission guide:source |
| w-a72f577613b8 | unhandled_screen_marker | `UI_Guide_C/InvalidationBox_0/Overlay_0` | 0.128, 0.371 → 0.200, 0.390 | 1 | mission guide:source |
| w-c35d807c87ef | unhandled_screen_marker | `UI_Lifebar_C/Border_0/SizeBox_0/ProgressBar_Boss` | 0.529, 0.396 → 0.596, 0.415 | 1 | none recorded |
| w-0be3f90b2e2e | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HorizontalBox_1/VerticalBox_1/HB_Healbar/Border_0/SizeBox_0/HealProgressBar` | 0.410, 0.918 → 0.581, 0.933 | 1 | none recorded |
| w-04f8d4e8982e | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HorizontalBox_1/VerticalBox_1/HB_Healbar/Border_0/SizeBox_0/HealProgressBar` | 0.409, 0.913 → 0.581, 0.928 | 1 | none recorded |
| w-28e7d096bf86 | unhandled_screen_marker | `UI_Lifebar_C/Border_0/SizeBox_0` | 0.473, 0.444 → 0.539, 0.462 | 1 | none recorded |
| w-a101974b82c5 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Moneys/HorizontalBox_463/Spacer` | 0.940, 0.061 → 0.951, 0.094 | 1 | none recorded |
| w-86119540b1d5 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Moneys/HorizontalBox_463/Spacer_127` | 0.902, 0.061 → 0.913, 0.094 | 1 | none recorded |
| w-c26c5e3f72a1 | edge_hud | `UI_BuildId_C/CanvasPanel_17/HorizontalBox_0/TextBlock_Id` | 0.904, 0.972 → 0.996, 0.993 | 1 | none recorded |
| w-06ccb63a41b2 | unhandled_screen_marker | `UI_Guide_C/InvalidationBox_0/Overlay_0/Border_0/InteractTextHolder` | 1.133, 0.292 → 1.185, 0.307 | 1 | mission guide:source |
| w-b345500cb7b6 | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/LoadingText` | 0.781, 0.822 → 0.948, 0.861 | 1 | none recorded |
| w-413c46377a8d | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox/TextBlock_Map` | 0.078, 0.139 → 0.274, 0.204 | 1 | none recorded |
| w-9466296d21b3 | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox_Difficulties/HorizontalBox_0/TextBlock_MissionAmont_Easy` | 0.913, 0.179 → 0.922, 0.212 | 1 | none recorded |
| w-aff35759a6c7 | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox_Difficulties/HorizontalBox_0/TextBlock_Missions_Easy` | 0.882, 0.179 → 0.909, 0.212 | 1 | none recorded |
| w-5d39fbabf0d1 | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox_Difficulties/HorizontalBox_1/TextBlock_MissionAmont_Normal` | 0.913, 0.212 → 0.922, 0.246 | 1 | none recorded |
| w-58127d3a1266 | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox_Difficulties/HorizontalBox_1/TextBlock_Missions_Normal` | 0.868, 0.212 → 0.908, 0.246 | 1 | none recorded |
| w-4d04b72c7f5e | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox_Difficulties/HorizontalBox_2/TextBlock_MissionAmount_Hard` | 0.913, 0.246 → 0.922, 0.279 | 1 | none recorded |
| w-ace2e2530160 | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox_Difficulties/HorizontalBox_2/TextBlock_Missions_Hard` | 0.880, 0.246 → 0.908, 0.279 | 1 | none recorded |
| w-a2868c109695 | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox_Difficulties/HorizontalBox_3/TextBlock_MissionAmount_VeryHard` | 0.913, 0.279 → 0.922, 0.312 | 1 | none recorded |
| w-dd92ebaa78f6 | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox_Difficulties/HorizontalBox_3/TextBlock_Missions_VeryHard` | 0.855, 0.279 → 0.908, 0.312 | 1 | none recorded |
| w-0fa9f706bdd4 | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox_Difficulties/HorizontalBox_4/TextBlock_MissionAmount_Nightmare` | 0.913, 0.312 → 0.922, 0.346 | 1 | none recorded |
| w-15a1523c11a8 | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox_Difficulties/HorizontalBox_4/TextBlock_Missions_Nightmare` | 0.851, 0.312 → 0.908, 0.346 | 1 | none recorded |
| w-0af4a2e74c8c | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox_Difficulties/TextBlock_Map_1` | 0.788, 0.139 → 0.922, 0.179 | 1 | none recorded |
| w-248a7ec027dc | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_1/HorizontalBox_35/Text_Legend` | 0.501, 0.957 → 0.561, 0.983 | 1 | none recorded |
| w-dcc61c548d5a | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_2/HorizontalBox_35/Text_Legend` | 0.386, 0.957 → 0.427, 0.983 | 1 | none recorded |
| w-38c509e5110e | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_3/HorizontalBox_35/Text_Legend` | 0.329, 0.957 → 0.360, 0.983 | 1 | none recorded |
| w-475a5f916760 | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_4/HorizontalBox_35/Text_Legend` | 0.453, 0.957 → 0.475, 0.983 | 1 | none recorded |
| w-5eeb60b6d372 | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_5/HorizontalBox_35/Text_Legend` | 0.659, 0.957 → 0.689, 0.983 | 1 | none recorded |
| w-29e8ae444ac5 | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_6/HorizontalBox_35/Text_Legend` | 0.587, 0.957 → 0.633, 0.983 | 1 | none recorded |
| w-9565b835031c | edge_hud | `UI_Map_C/CanvasPanel_36/TextBlock_MapName` | 0.478, 0.014 → 0.522, 0.051 | 1 | none recorded |
| w-74987202022a | edge_hud | `UI_Map_C/CanvasPanel_36/Text_Difficulty` | 0.908, 0.019 → 0.990, 0.052 | 1 | none recorded |
| w-5fd64a205a30 | edge_hud | `UI_MissionStart_C/CanvasPanel_30/TextBlock_Countdown` | 0.411, 0.873 → 0.589, 0.926 | 1 | none recorded |
| w-38c6b743d3d3 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key` | 0.047, 0.833 → 0.055, 0.860 | 1 | none recorded |
| w-8a490d206b08 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key_1` | 0.062, 0.833 → 0.066, 0.856 | 1 | none recorded |
| w-80792ba812e6 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key_2` | 0.042, 0.833 → 0.046, 0.856 | 1 | none recorded |
| w-60cb6ef71fd4 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/HorizontalBox_Holder/Name` | 0.069, 0.835 → 0.103, 0.857 | 1 | none recorded |
| w-98b97f194c19 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key` | 0.054, 0.868 → 0.061, 0.896 | 1 | none recorded |
| w-22000c94f502 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key_1` | 0.069, 0.868 → 0.073, 0.892 | 1 | none recorded |
| w-9a8653e15d72 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key_2` | 0.049, 0.868 → 0.053, 0.891 | 1 | none recorded |
| w-de070bbbb4a4 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/HorizontalBox_Holder/Name` | 0.077, 0.870 → 0.113, 0.892 | 1 | none recorded |
| w-8850f6a8cc8f | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key` | 0.061, 0.903 → 0.068, 0.931 | 1 | none recorded |
| w-bbd600438daf | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key_1` | 0.100, 0.904 → 0.104, 0.927 | 1 | none recorded |
| w-a36410c31ad3 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key_2` | 0.080, 0.904 → 0.084, 0.927 | 1 | none recorded |
| w-54d75562c5da | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/HorizontalBox_Holder/Name` | 0.107, 0.906 → 0.129, 0.928 | 1 | none recorded |
| w-46599b62abeb | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HorizontalBox_1/VerticalBox_1/HB_Healbar/SizeBox_2/Text_PlayerHeal` | 0.379, 0.913 → 0.407, 0.937 | 1 | none recorded |
| w-83607dcfaab5 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox/GoldAmount` | 0.842, 0.062 → 0.875, 0.085 | 1 | none recorded |
| w-1b36102208b2 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_1/TextLevel` | 0.627, 0.062 → 0.657, 0.084 | 1 | none recorded |
| w-7d88a73d1bc9 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_2/SoulAmount` | 0.768, 0.062 → 0.810, 0.084 | 1 | none recorded |
| w-9147fa5f0dbf | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_3/TicketAmount` | 0.688, 0.062 → 0.737, 0.084 | 1 | none recorded |
| w-ef64cef6bcc0 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_6/BlueprintAmount` | 0.906, 0.062 → 0.961, 0.085 | 1 | none recorded |
| w-ad838bf8a18c | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes/Text_Emotes` | 0.905, 0.786 → 0.931, 0.809 | 1 | none recorded |
| w-eb7a9bb2713d | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes/UI_Key_Emotes/HorizontalBox_2/Text_Key` | 0.943, 0.780 → 0.950, 0.805 | 1 | none recorded |
| w-6e003d0ff33d | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes/UI_Key_Emotes/HorizontalBox_2/Text_Key_1` | 0.950, 0.781 → 0.953, 0.802 | 1 | none recorded |
| w-93bcac3844ac | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes/UI_Key_Emotes/HorizontalBox_2/Text_Key_2` | 0.932, 0.782 → 0.935, 0.802 | 1 | none recorded |
| w-bd5665f29570 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/HB_Battlecry_Gamepad/Text_Emotes_2` | 0.925, 0.817 → 0.932, 0.840 | 1 | none recorded |
| w-c67619c219f9 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/HB_Battlecry_Gamepad/UI_Key_BattleCry/HorizontalBox_2/Text_Key_1` | 0.919, 0.812 → 0.923, 0.833 | 1 | none recorded |
| w-298ca68851ec | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/HB_Battlecry_Gamepad/UI_Key_BattleCry/HorizontalBox_2/Text_Key_2` | 0.902, 0.812 → 0.905, 0.833 | 1 | none recorded |
| w-1cdf8543c46c | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/HB_Battlecry_Gamepad/UI_Key_BattleCry_2/HorizontalBox_2/Text_Key_1` | 0.951, 0.812 → 0.954, 0.833 | 1 | none recorded |
| w-c610b39a72da | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/HB_Battlecry_Gamepad/UI_Key_BattleCry_2/HorizontalBox_2/Text_Key_2` | 0.933, 0.812 → 0.936, 0.833 | 1 | none recorded |
| w-17869750945a | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/HB_Battlecry_PC/UI_Key_BattleCry_1/HorizontalBox_2/Text_Key` | 0.942, 0.810 → 0.950, 0.835 | 1 | none recorded |
| w-43668cf482ea | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/HB_Battlecry_PC/UI_Key_BattleCry_1/HorizontalBox_2/Text_Key_1` | 0.950, 0.811 → 0.953, 0.831 | 1 | none recorded |
| w-b49c56327f73 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/HB_Battlecry_PC/UI_Key_BattleCry_1/HorizontalBox_2/Text_Key_2` | 0.939, 0.811 → 0.942, 0.831 | 1 | none recorded |
| w-f365957807c5 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/Text_Emotes_1` | 0.863, 0.816 → 0.900, 0.839 | 1 | none recorded |
| w-d81358ddade6 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Melee/Text_Melee` | 0.906, 0.847 → 0.931, 0.870 | 1 | none recorded |
| w-685796d7fa5b | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Melee/UI_Key_Melee/HorizontalBox_2/Text_Key` | 0.943, 0.840 → 0.950, 0.865 | 1 | none recorded |
| w-d090fbbe8095 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Melee/UI_Key_Melee/HorizontalBox_2/Text_Key_1` | 0.951, 0.842 → 0.954, 0.863 | 1 | none recorded |
| w-6939a72dd8f3 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Melee/UI_Key_Melee/HorizontalBox_2/Text_Key_2` | 0.933, 0.842 → 0.937, 0.863 | 1 | none recorded |
| w-14b53b687ecf | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Quests/Text_Quest` | 0.888, 0.877 → 0.931, 0.900 | 1 | none recorded |
| w-963218204140 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Quests/UI_key_Quest/HorizontalBox_2/Text_Key` | 0.932, 0.870 → 0.950, 0.895 | 1 | none recorded |
| w-5b30e62f286f | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Quests/UI_key_Quest/HorizontalBox_2/Text_Key_1` | 0.951, 0.873 → 0.954, 0.893 | 1 | none recorded |
| w-ce4281587aca | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Quests/UI_key_Quest/HorizontalBox_2/Text_Key_2` | 0.933, 0.873 → 0.937, 0.893 | 1 | none recorded |
| w-5b1fe51e94ba | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/HB_Ammo/Text_CurrentAmmos` | 0.891, 0.901 → 0.960, 0.931 | 1 | none recorded |
| w-5c56b75bbdb9 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/Border_110/HorizontalBox_0/TextBlock_KillCounter` | 0.314, 0.914 → 0.314, 0.914 | 1 | none recorded |
| w-3cbbe2b02a75 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Moneys/HorizontalBox_463/TextBlock_GoldAmount` | 0.892, 0.070 → 0.897, 0.091 | 1 | none recorded |
| w-8e10776fb906 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Moneys/HorizontalBox_463/TextBlock_SoulAmount` | 0.929, 0.067 → 0.935, 0.088 | 1 | none recorded |
| w-508ce206d343 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Moneys/HorizontalBox_463/TextBlock_UraniumAmount` | 0.968, 0.070 → 0.973, 0.091 | 1 | none recorded |
| w-a177f9071d24 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/CooldownText` | 0.030, 0.838 → 0.035, 0.859 | 1 | none recorded |
| w-2624390ea191 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key` | 0.050, 0.836 → 0.058, 0.864 | 1 | none recorded |
| w-16c0a8bdbc4a | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key_1` | 0.068, 0.833 → 0.072, 0.856 | 1 | none recorded |
| w-013f9bc7ef73 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key_2` | 0.048, 0.833 → 0.052, 0.856 | 1 | none recorded |
| w-159e3ee36663 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/HorizontalBox_Holder/Name` | 0.070, 0.833 → 0.103, 0.855 | 1 | none recorded |
| w-ea57d163e185 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/CooldownText` | 0.037, 0.872 → 0.042, 0.893 | 1 | none recorded |
| w-556628f6c70e | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key` | 0.057, 0.872 → 0.065, 0.899 | 1 | none recorded |
| w-80aa5c127649 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key_1` | 0.075, 0.869 → 0.079, 0.892 | 1 | none recorded |
| w-20974f8f3f8d | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key_2` | 0.055, 0.868 → 0.059, 0.892 | 1 | none recorded |
| w-607e3cff2907 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/HorizontalBox_Holder/Name` | 0.077, 0.869 → 0.113, 0.891 | 1 | none recorded |
| w-4b4e6efa769f | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/CooldownText` | 0.044, 0.907 → 0.048, 0.928 | 1 | none recorded |
| w-50c0adb45274 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key` | 0.064, 0.907 → 0.071, 0.935 | 1 | none recorded |
| w-69b372a5ca49 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key_1` | 0.104, 0.903 → 0.108, 0.926 | 1 | none recorded |
| w-78af071b45ec | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C/HorizontalBox_2/Text_Key_2` | 0.084, 0.902 → 0.088, 0.926 | 1 | none recorded |
| w-311757b87eac | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/HorizontalBox_Holder/Name` | 0.108, 0.904 → 0.129, 0.926 | 1 | none recorded |
| w-d26e9c8e13fa | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HorizontalBox_1/VerticalBox_1/HB_Healbar/SizeBox_2/Text_PlayerHeal` | 0.382, 0.909 → 0.407, 0.933 | 1 | none recorded |
| w-63ce7fbfe7ce | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/HB_Ammo/Text_CurrentAmmos` | 0.896, 0.897 → 0.961, 0.927 | 1 | none recorded |
| w-2198c2fb5a06 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_Grenades/GrenadeAmount` | 0.888, 0.871 → 0.933, 0.892 | 1 | none recorded |
| w-058b769d60ca | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_Grenades/UI_Key_2/HorizontalBox_2/Text_Key` | 0.945, 0.866 → 0.953, 0.894 | 1 | none recorded |
| w-03a261f234f2 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_Grenades/UI_Key_2/HorizontalBox_2/Text_Key_1` | 0.955, 0.865 → 0.959, 0.889 | 1 | none recorded |
| w-e8832cf07f1b | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_Grenades/UI_Key_2/HorizontalBox_2/Text_Key_2` | 0.935, 0.865 → 0.939, 0.888 | 1 | none recorded |
| w-2e65f911e8f1 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_Map/UI_Key/HorizontalBox_2/Text_Key` | 0.933, 0.835 → 0.953, 0.863 | 1 | none recorded |
| w-298eb3041c3b | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_Map/UI_Key/HorizontalBox_2/Text_Key_1` | 0.955, 0.835 → 0.959, 0.858 | 1 | none recorded |
| w-22bb237fc1e1 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_Map/UI_Key/HorizontalBox_2/Text_Key_2` | 0.936, 0.835 → 0.939, 0.858 | 1 | none recorded |
| w-b3f6e69f602d | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_Map/textMap` | 0.916, 0.841 → 0.933, 0.862 | 1 | none recorded |
| w-a4f98e82de39 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_MapAndHorse/UI_Key_1/HorizontalBox_2/Text_Key` | 0.945, 0.804 → 0.954, 0.832 | 1 | none recorded |
| w-547d18c4df5d | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_MapAndHorse/UI_Key_1/HorizontalBox_2/Text_Key_1` | 0.956, 0.805 → 0.959, 0.828 | 1 | none recorded |
| w-76965813e30a | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_MapAndHorse/UI_Key_1/HorizontalBox_2/Text_Key_2` | 0.936, 0.806 → 0.939, 0.829 | 1 | none recorded |
| w-cd8cf9f31193 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_MapAndHorse/textMap_1` | 0.884, 0.811 → 0.933, 0.832 | 1 | none recorded |
| w-47456db5d47a | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_Region_Brimtstone/VerticalBox_0/Button_Hover/VerticalBox_1/Border_Region/Border_Background/HorizontalBox_0/Text_Name` | 1.051, 0.741 → 1.087, 0.763 | 1 | none recorded |
| w-907a1eb20784 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_Region_FarFarNorth/VerticalBox_0/Button_Hover/VerticalBox_1/Border_Region/Border_Background/HorizontalBox_0/Text_Name` | 0.673, 0.132 → 0.733, 0.155 | 1 | none recorded |
| w-25fb16f4d743 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_Region_Jungle/VerticalBox_0/Button_Hover/VerticalBox_1/Border_Region/Border_Background/HorizontalBox_0/Text_Name` | 0.926, 0.388 → 0.955, 0.410 | 1 | none recorded |
| w-8eb185ee6d0f | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_Region_Woodlands/VerticalBox_0/Button_Hover/VerticalBox_1/Border_Region/Border_Background/HorizontalBox_0/Text_Name` | 0.658, 0.850 → 0.708, 0.872 | 1 | none recorded |
| w-762bc108bcdd | edge_hud | `UI_StartMission_C/CanvasPanel_0/HorizontalBox_3/Button_DifficultyHover/Border_DifficultyGlow/Border_Difficulty/HorizontalBox_1/HorizontalBox_65/TextDifficulty` | 0.524, 0.872 → 0.556, 0.909 | 1 | none recorded |
| w-ce4e8a7820c0 | edge_hud | `UI_StartMission_C/CanvasPanel_0/HorizontalBox_3/Button_DifficultyHover/Border_DifficultyGlow/Border_Difficulty/HorizontalBox_1/TextBlock` | 0.418, 0.872 → 0.489, 0.909 | 1 | none recorded |
| w-a33f29788fc1 | edge_hud | `UI_StartMission_C/CanvasPanel_0/HorizontalBox_4/TextBlock_389` | 0.863, 0.083 → 0.990, 0.117 | 1 | none recorded |
| w-25200b915f15 | edge_hud | `UI_StartMission_C/CanvasPanel_0/UI_Equipment_GoBack/Button_GoBack/HorizontalBox_0/TextBlock_53` | 0.027, 0.020 → 0.055, 0.050 | 1 | none recorded |
| w-563c6755aafc | edge_hud | `UI_StartMission_C/CanvasPanel_0/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox/GoldAmount` | 0.849, 0.021 → 0.883, 0.045 | 1 | none recorded |
| w-2a8c312bbb43 | edge_hud | `UI_StartMission_C/CanvasPanel_0/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_1/TextLevel` | 0.627, 0.021 → 0.658, 0.045 | 1 | none recorded |
| w-7cabfe4728d9 | edge_hud | `UI_StartMission_C/CanvasPanel_0/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_2/SoulAmount` | 0.773, 0.021 → 0.817, 0.045 | 1 | none recorded |
| w-7a781a73a14d | edge_hud | `UI_StartMission_C/CanvasPanel_0/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_3/TicketAmount` | 0.691, 0.021 → 0.741, 0.045 | 1 | none recorded |
| w-9a23bedbd3f2 | edge_hud | `UI_StartMission_C/CanvasPanel_0/UI_Equipment_PlayerStats/InvalidationBox_0/VerticalBox_1/Button_Hover/VerticalBox_0/HorizontalBox_0/HorizontalBox_6/BlueprintAmount` | 0.915, 0.021 → 0.972, 0.045 | 1 | none recorded |
| w-806f549e5496 | edge_hud | `UI_StartMission_C/CanvasPanel_0/VerticalBox_0/UI_Template_GenerateContracts/Button_Tab/Border_Color/HorizontalBox_Content/TextBlock_Text` | 0.861, 0.879 → 0.979, 0.904 | 1 | none recorded |
| w-820fc12f3097 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_117/TextBlock_4` | 0.337, 0.184 → 0.926, 0.304 | 1 | none recorded |
| w-ad4e34cd69c5 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_117/TextBlock_9` | 0.337, 0.131 → 0.687, 0.184 | 1 | none recorded |
| w-c717776388c9 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/VerticalBox_0/TextBlock` | 0.626, 0.665 → 0.934, 0.727 | 1 | none recorded |
| w-42e4f007362c | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/VerticalBox_0/UI_Template_Discord/Button_Tab/Overlay_0/Border_Color/Border_Padding/HorizontalBox_0/TextBlock_Text` | 0.828, 0.766 → 0.924, 0.796 | 1 | none recorded |
| w-a03e0b675543 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/VerticalBox_0/UI_Template_PatchNote/Button_Tab/Overlay_0/Border_Color/Border_Padding/HorizontalBox_0/TextBlock_Text` | 0.771, 0.844 → 0.924, 0.874 | 1 | none recorded |
| w-6bbb9b7c5634 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_WelcomeScreen_C/Overlay_52/Overlay_0/VerticalBox/HorizontalBox_0/TextBlock_5` | 0.172, 0.141 → 0.543, 0.268 | 1 | none recorded |
| w-a2a34f763f77 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_WelcomeScreen_C/Overlay_52/Overlay_0/VerticalBox/HorizontalBox_1/VerticalBox_0/TextBlock_1` | 0.253, 0.823 → 0.747, 0.859 | 1 | none recorded |
| w-cede8e4a450e | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/UI_Equipment_GoBack/Button_GoBack/HorizontalBox_0/TextBlock_53` | 0.027, 0.020 → 0.055, 0.050 | 1 | none recorded |
| w-89ae647dbe9b | edge_hud | `UI_Equipment_Tweak_Hero_C/CanvasPanel_36/GoBackButton` | 0.006, 0.011 → 0.061, 0.059 | 1 | none recorded |
| w-83c82ff42c1e | edge_hud | `UI_StartMission_C/CanvasPanel_0/UI_Equipment_GoBack` | 0.006, 0.011 → 0.061, 0.059 | 1 | none recorded |
| w-585fb2719872 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/UI_Equipment_GoBack` | 0.006, 0.011 → 0.061, 0.059 | 1 | none recorded |
| w-7531880b7918 | edge_hud | `UI_Equipment_Tweak_Hero_C/CanvasPanel_36/UI_Equipment_PlayerStats` | 0.625, 0.019 → 0.990, 0.048 | 1 | none recorded |
| w-f7457ab58aa0 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/UI_Equipment_PlayerStats` | 0.623, 0.055 → 0.976, 0.082 | 1 | none recorded |
| w-eb8884e426c9 | edge_hud | `UI_StartMission_C/CanvasPanel_0/UI_Equipment_PlayerStats` | 0.625, 0.019 → 0.990, 0.048 | 1 | none recorded |
| w-ae61c77494de | edge_hud | `UI_Equipment_Tweak_Hero_C/CanvasPanel_36/NamedSlot_63/CanvasPanel_46/VerticalBox_1/UniformGridPanel_Jokers/UI_Joker_Slot_C` | 0.865, 0.767 → 0.902, 0.833 | 1 | none recorded |
| w-456e02f273b9 | edge_hud | `UI_Equipment_Tweak_Hero_C/CanvasPanel_36/NamedSlot_63/CanvasPanel_46/Border_1/VerticalBox_3/VerticalBox_0/Border_0/VerticalBox_2/VerticalBox_Shops/UI_Tweak_ShopLine_C` | 0.068, 0.565 → 0.502, 0.617 | 1 | none recorded |
| w-58c4c145f76d | edge_hud | `UI_Leaderboard_C/Canvas/WidgetSwitcherLeaderboard/PanelXp/VerticalBox_Bars/UI_Leaderboard_LevelProgress_C` | 0.436, 0.286 → 0.950, 0.374 | 1 | none recorded |
| w-3004a619f5d3 | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_1` | 0.479, 0.950 → 0.565, 0.991 | 1 | none recorded |
| w-05b70b045276 | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_2` | 0.364, 0.950 → 0.431, 0.991 | 1 | none recorded |
| w-d7f839761d15 | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_3` | 0.307, 0.950 → 0.364, 0.991 | 1 | none recorded |
| w-be3cc0572e91 | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_4` | 0.431, 0.950 → 0.479, 0.991 | 1 | none recorded |
| w-a9a80b58abfb | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_5` | 0.637, 0.950 → 0.693, 0.991 | 1 | none recorded |
| w-927367ca3e48 | edge_hud | `UI_Map_C/CanvasPanel_36/HorizontalBox_0/UI_Map_Legend_6` | 0.565, 0.950 → 0.637, 0.991 | 1 | none recorded |
| w-1f16f81b9e91 | edge_hud | `UI_Map_C/CanvasPanel_36/SizeBox_141/Overlay_Map/UI_Map_Line_C` | 0.205, 0.262 → 0.474, 0.607 | 1 | none recorded |
| w-d9273813aa17 | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox/UI_Map_Task_Bounty_2` | 0.078, 0.265 → 0.192, 0.326 | 1 | none recorded |
| w-82bef7f9b1b8 | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox/UI_Map_Task_Extract_1` | 0.078, 0.326 → 0.170, 0.387 | 1 | none recorded |
| w-1346a5dc65f3 | edge_hud | `UI_LoadingScreen_C/CanvasPanel_30/VerticalBox/UI_Map_Task_Reveal_1` | 0.078, 0.204 → 0.225, 0.265 | 1 | none recorded |
| w-328ac978600f | unhandled_screen_marker | `UI_PingObjective_C` | 0.272, 0.574 → 0.315, 0.626 | 1 | objective marker:source |
| w-d462ac99454f | edge_hud | `UI_StartMission_C/CanvasPanel_0/HorizontalBox_3/Button_DifficultyHover/Border_DifficultyGlow/Border_Difficulty/HorizontalBox_1/HorizontalBox_65/UI_StartMission_DifficultyArrow_Left` | 0.498, 0.868 → 0.524, 0.914 | 1 | none recorded |
| w-a0321d15586d | edge_hud | `UI_StartMission_C/CanvasPanel_0/HorizontalBox_3/Button_DifficultyHover/Border_DifficultyGlow/Border_Difficulty/HorizontalBox_1/HorizontalBox_65/UI_StartMission_DifficultyArrow_Right` | 0.556, 0.868 → 0.582, 0.914 | 1 | none recorded |
| w-7a8601a9f0a9 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_RegionImage_` | 0.927, 0.385 → 1.207, 0.884 | 1 | none recorded |
| w-9d7316d6a1f6 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_RegionImage_Area41` | 0.154, 0.478 → 0.474, 1.047 | 1 | none recorded |
| w-7e4e6856796e | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_RegionImage_Desert` | 0.355, 0.356 → 0.675, 0.924 | 1 | none recorded |
| w-2afab819fb33 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_RegionImage_FarFarNorth` | 0.533, -0.124 → 0.853, 0.444 | 1 | none recorded |
| w-bb4e133f8877 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_RegionImage_FarWest` | 0.305, 0.144 → 0.625, 0.713 | 1 | none recorded |
| w-3407213f0218 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_RegionImage_Jungle` | 0.824, 0.180 → 1.105, 0.680 | 1 | none recorded |
| w-a3ebc14fd863 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_RegionImage_Woodlands` | 0.530, 0.378 → 0.890, 1.017 | 1 | none recorded |
| w-c38a37015123 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_Region_Area41` | 0.137, 0.771 → 0.453, 0.913 | 1 | none recorded |
| w-20da51ea3143 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_Region_Brimtstone` | 0.926, 0.696 → 1.212, 0.838 | 1 | none recorded |
| w-d4f64ba0899c | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_Region_FarFarNorth` | 0.499, 0.087 → 0.907, 0.229 | 1 | none recorded |
| w-49e7fe2f9bc0 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_Region_Jungle` | 0.781, 0.342 → 1.100, 0.484 | 1 | none recorded |
| w-a48005425802 | edge_hud | `UI_StartMission_C/CanvasPanel_0/CanvasPanel_Map/UI_Region_Woodlands` | 0.531, 0.804 → 0.835, 0.947 | 1 | none recorded |
| w-5c3699497286 | unhandled_screen_marker | `UI_Guide_C` | 0.444, 0.173 → 0.557, 0.192 | 1 | mission guide:source |
| w-fd7113bb1e4f | interact_keyboard_hint | `UI_Interact_C/InvalidationBox_0/VerticalBox_56/Overlay_101/HorizontalBox_69/UI_Key` | 0.502, 0.468 → 0.525, 0.486 | 1 | UI_Interact_C:source |
| w-b6169b49d5a6 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C` | 0.044, 0.832 → 0.067, 0.859 | 1 | none recorded |
| w-df4a351d8be0 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C` | 0.051, 0.868 → 0.075, 0.895 | 1 | none recorded |
| w-4654c0082cd9 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C` | 0.082, 0.903 → 0.106, 0.930 | 1 | none recorded |
| w-27c141b299ff | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes/UI_Key_Emotes` | 0.934, 0.785 → 0.955, 0.809 | 1 | none recorded |
| w-4c2f53d8afdb | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/HB_Battlecry_Gamepad/UI_Key_BattleCry` | 0.903, 0.816 → 0.925, 0.840 | 1 | none recorded |
| w-fcb7761835ad | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/HB_Battlecry_Gamepad/UI_Key_BattleCry_2` | 0.934, 0.816 → 0.955, 0.840 | 1 | none recorded |
| w-48b89e77a37e | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Emotes_2/HB_Battlecry_PC/UI_Key_BattleCry_1` | 0.939, 0.810 → 0.953, 0.835 | 1 | none recorded |
| w-09507df0ec15 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Melee/UI_Key_Melee` | 0.934, 0.845 → 0.955, 0.869 | 1 | none recorded |
| w-945e1aff8869 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/NamedSlot_216/CanvasPanel_86/VB_Lobby/HB_Quests/UI_key_Quest` | 0.934, 0.876 → 0.955, 0.900 | 1 | none recorded |
| w-5ff5be4cfdd5 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C` | 0.048, 0.831 → 0.072, 0.858 | 1 | none recorded |
| w-6e36ea8f1334 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C` | 0.055, 0.867 → 0.079, 0.894 | 1 | none recorded |
| w-02e00b213592 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown/Overlay_1/HorizontalBox_Holder/HorizontalBox_Keys/UI_Key_C` | 0.082, 0.899 → 0.106, 0.926 | 1 | none recorded |
| w-3123b79f562e | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_Grenades/UI_Key_2` | 0.934, 0.870 → 0.957, 0.897 | 1 | none recorded |
| w-c8369c6362c4 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_Map/UI_Key` | 0.934, 0.840 → 0.957, 0.867 | 1 | none recorded |
| w-90370fc3782f | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/VerticalBox_0/VerticalBox_Weapons/HB_MapAndHorse/UI_Key_1` | 0.934, 0.810 → 0.957, 0.836 | 1 | none recorded |
| w-c03422b09577 | unhandled_screen_marker | `UI_Lifebar_C` | 0.582, 0.400 → 0.650, 0.429 | 1 | none recorded |
| w-e6681a39383e | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown` | 0.022, 0.829 → 0.104, 0.860 | 1 | none recorded |
| w-a3ae9585ce59 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown` | 0.029, 0.865 → 0.114, 0.895 | 1 | none recorded |
| w-6b7ee8d3bed2 | edge_hud | `UI_PlayerLobby_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown` | 0.036, 0.900 → 0.130, 0.931 | 1 | none recorded |
| w-71128765565f | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellA_Cooldown` | 0.025, 0.829 → 0.107, 0.859 | 1 | none recorded |
| w-248a357725f1 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellB_Cooldown` | 0.033, 0.864 → 0.118, 0.895 | 1 | none recorded |
| w-2be18f525844 | edge_hud | `UI_Player_C/CanvasPanel_39/RetainerBox_0/DPIScalerBox_2/MovingCanvas/HB_Spells/SpellC_Cooldown` | 0.040, 0.899 → 0.133, 0.930 | 1 | none recorded |
| w-0f4e917ed15a | edge_hud | `UI_Leaderboard_C/Canvas/HorizontalBox_SwitcherButtons/UI_Template_Button_Continue` | 0.885, 0.830 → 0.967, 0.881 | 1 | none recorded |
| w-98cac8e4ed53 | edge_hud | `UI_Leaderboard_C/Canvas/HorizontalBox_SwitcherButtons/UI_Template_Button_Stats` | 0.818, 0.830 → 0.885, 0.881 | 1 | none recorded |
| w-b3fa72bc9201 | edge_hud | `UI_Leaderboard_C/Canvas/HorizontalBox_SwitcherButtons/UI_Template_Button_Summary` | 0.732, 0.830 → 0.818, 0.881 | 1 | none recorded |
| w-b188a648c0ba | edge_hud | `UI_StartMission_C/CanvasPanel_0/VerticalBox_0/UI_Template_GenerateContracts` | 0.831, 0.865 → 0.990, 0.917 | 1 | none recorded |
| w-042f7f6a813f | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_116/UI_Template_BroweSessions` | 0.074, 0.454 → 0.304, 0.532 | 1 | none recorded |
| w-6be298911cba | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_116/UI_Template_CreateSession` | 0.074, 0.376 → 0.304, 0.454 | 1 | none recorded |
| w-bf9f93e1c78f | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_116/UI_Template_Credits` | 0.074, 0.688 → 0.304, 0.766 | 1 | none recorded |
| w-8711e4bd0ba1 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_116/UI_Template_Options` | 0.074, 0.610 → 0.304, 0.688 | 1 | none recorded |
| w-12e4bc97a5dc | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_116/UI_Template_Quit` | 0.074, 0.766 → 0.304, 0.844 | 1 | none recorded |
| w-658e740d3db6 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/HorizontalBox_1/VerticalBox_116/UI_Template_Tutorial` | 0.074, 0.532 → 0.304, 0.610 | 1 | none recorded |
| w-ab52c3a60ba3 | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/VerticalBox_0/UI_Template_Discord` | 0.781, 0.742 → 0.943, 0.820 | 1 | none recorded |
| w-b0dfc14fa3ad | edge_hud | `UI_TitleScreen_C/CanvasPanel_36/Holder/UI_Menu_Container_TitleScreen_C/CanvasPanel_0/VerticalBox_0/UI_Template_PatchNote` | 0.724, 0.820 → 0.943, 0.898 | 1 | none recorded |
| w-33e745de4779 | unhandled_screen_marker | `UI_WorldIcon_C` | 0.248, 0.366 → 0.265, 0.385 | 1 | UI_WorldIcon_C:proxy, UI_WorldIcon_C:source |

</details>
