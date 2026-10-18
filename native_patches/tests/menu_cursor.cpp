// Run against the retained UEVR checkout and its built imgui.lib; no game needed.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#define IMGUI_USER_CONFIG "uevr_imconfig.hpp"
#include <windows.h>
#include <cstdlib>
#include <iostream>
#include "ffw_menu_cursor.hpp"

static void check(bool passed, const char* message) {
    if (!passed) { std::cerr << message << '\n'; std::exit(1); }
}

int wmain(int argc, wchar_t** argv) {
    check(argc == 2, "Pass the cursor PNG path.");
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    auto& io = ImGui::GetIO();
    FfwMenuCursor cursor;
    // Exercise the same decode/build/upload sequence twice (font/device rebuild).
    for (int pass = 0; pass < 2; ++pass) {
        io.Fonts->Clear();
        io.Fonts->AddFontDefault();
        check(cursor.reserve(io.Fonts, argv[1]), "WIC could not load the supplied PNG.");
        const auto original = cursor.rgba;
        const auto width = cursor.width, height = cursor.height;
        check(width == 128 && height == 128, "Unexpected source dimensions.");
        bool transparent = false, colored = false;
        for (size_t i = 0; i < original.size(); i += 4) {
            transparent |= original[i + 3] == 0;
            colored |= original[i + 3] > 0 && original[i] != original[i + 2];
        }
        check(transparent && colored, "Source alpha/color was lost.");
        check(io.Fonts->Build(), "Font atlas build failed.");
        cursor.fill(io.Fonts);
        auto* packed = io.Fonts->GetCustomRectByIndex(cursor.rect);
        auto* pixels = reinterpret_cast<unsigned char*>(io.Fonts->TexPixelsRGBA32);
        for (UINT y = 0; y < height + 2; ++y) {
            for (UINT x = 0; x < width + 2; ++x) {
                auto* pixel = pixels + ((packed->Y + y) * io.Fonts->TexWidth + packed->X + x) * 4;
                if (!x || !y || x == width + 1 || y == height + 1) {
                    check(pixel[0] == 0 && pixel[1] == 0 && pixel[2] == 0 && pixel[3] == 0,
                        "Transparent gutter contaminated.");
                } else {
                    check(std::memcmp(pixel, original.data() + ((y - 1) * width + x - 1) * 4, 4) == 0,
                        "Decoded pixels changed in the atlas.");
                }
            }
        }
        io.Fonts->SetTexID((ImTextureID)42);
        io.DisplaySize = ImVec2(2560, 1440);
        io.DeltaTime = 1.0f / 90;
        io.MousePos = ImVec2(640, 360);
        ImGui::NewFrame();
        check(cursor.draw(), "Cursor draw failed.");
        const auto* list = ImGui::GetForegroundDrawList();
        check(list->VtxBuffer.Size == 4 && list->IdxBuffer.Size == 6, "Expected one image quad.");
        check(list->VtxBuffer[0].pos.x == 640 && list->VtxBuffer[0].pos.y == 360,
            "Top-left click hotspot shifted.");
        check(list->VtxBuffer[2].pos.x == 688 && list->VtxBuffer[2].pos.y == 408,
            "Unexpected display size.");
        ImGui::EndFrame();
        check(!cursor.reserve(io.Fonts, L"ffw-missing-cursor.png"), "Missing image did not fall back.");
        check(cursor.rect == -1, "Missing image retained a stale atlas rectangle.");
        ImGui::NewFrame();
        check(!cursor.draw(), "Missing image suppressed the standard cursor.");
        ImGui::EndFrame();
    }
    ImGui::DestroyContext();
    std::cout << "Cursor PNG/color/alpha, atlas gutter/rebuild, hotspot/size and fallback passed.\n";
}
