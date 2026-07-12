#include <mystream/plugin_api.hpp>

#include <cstddef>
#include <cstdlib>
#include <string>
#include <vector>

namespace {
struct SystemInfoPanelInstance { };

std::string ReadHostJson(
    const mystream::plugin::PluginPanelHostApi* host,
    const char* key) {
    if (!host || !host->get_json) {
        return {};
    }
    std::size_t requiredSize = 0;
    if (!host->get_json(host->userData, key, nullptr, 0, &requiredSize) || requiredSize == 0) {
        return {};
    }
    std::vector<char> buffer(requiredSize);
    if (!host->get_json(host->userData, key, buffer.data(), buffer.size(), &requiredSize)) {
        return {};
    }
    return buffer.data();
}

std::string JsonString(const std::string& json, const std::string& key) {
    const std::string prefix = "\"" + key + "\":\"";
    const std::size_t begin = json.find(prefix);
    if (begin == std::string::npos) {
        return {};
    }
    const std::size_t valueBegin = begin + prefix.size();
    const std::size_t valueEnd = json.find('"', valueBegin);
    return valueEnd == std::string::npos ? std::string() : json.substr(valueBegin, valueEnd - valueBegin);
}

int JsonInt(const std::string& json, const std::string& key) {
    const std::string prefix = "\"" + key + "\":";
    const std::size_t begin = json.find(prefix);
    if (begin == std::string::npos) {
        return 0;
    }
    return std::atoi(json.c_str() + begin + prefix.size());
}

void* CreatePanel() {
    return new SystemInfoPanelInstance();
}

void DestroyPanel(void* instance) {
    delete static_cast<SystemInfoPanelInstance*>(instance);
}

void RenderPanel(
    void*,
    const mystream::plugin::PluginUiApi* ui,
    const mystream::plugin::PluginPanelHostApi* host) {
    if (!ui || ui->apiVersion < mystream::plugin::kPluginApiVersionV12) {
        return;
    }

    const std::string snapshot = ReadHostJson(host, "system.info.snapshot");
    const std::string application = JsonString(snapshot, "application");
    const std::string platform = JsonString(snapshot, "platform");
    const std::string sdkVersion = JsonString(snapshot, "sdkVersion");
    const std::string status = JsonString(snapshot, "status");
    const int pluginApi = JsonInt(snapshot, "pluginApi");
    const int loadedPlugins = JsonInt(snapshot, "loadedPlugins");

    ui->status_indicator(
        status.empty() ? "Host unavailable" : "Application running",
        status.empty() ? 0.95f : 0.25f,
        status.empty() ? 0.35f : 0.85f,
        0.35f,
        1.0f);
    ui->spacing();

    if (ui->begin_child("system_overview", 0.0f, 132.0f, true)) {
        ui->text_colored("SYSTEM", 0.45f, 0.68f, 1.0f, 1.0f);
        ui->separator();
        ui->label_value("Application", application.empty() ? "Unknown" : application.c_str());
        ui->label_value("Platform", platform.empty() ? "Unknown" : platform.c_str());
        ui->label_value("Status", status.empty() ? "Unavailable" : status.c_str());
    }
    ui->end_child();
    ui->spacing();

    if (ui->begin_child("plugin_runtime", 0.0f, 150.0f, true)) {
        ui->text_colored("PLUGIN RUNTIME", 0.70f, 0.45f, 1.0f, 1.0f);
        ui->separator();
        const std::string apiValue = pluginApi > 0 ? std::to_string(pluginApi) : "Unknown";
        const std::string pluginCount = std::to_string(loadedPlugins);
        ui->label_value("SDK", sdkVersion.empty() ? "Unknown" : sdkVersion.c_str());
        ui->label_value("API", apiValue.c_str());
        ui->label_value("Loaded plugins", pluginCount.c_str());
        ui->spacing();
        ui->progress_bar(1.0f, "Panel API connected", -1.0f, 0.0f);
    }
    ui->end_child();

    ui->spacing();
    ui->text_disabled("This panel is rendered entirely by an installable plugin.");
}
}

extern "C" bool mystream_register_plugin_v12(mystream::plugin::PluginApiV12* api) {
    if (!api || api->apiVersion != mystream::plugin::kPluginApiVersionV12 || !api->register_panel) {
        return false;
    }
    mystream::plugin::PluginPanelDefinition definition{};
    definition.id = "mystream.panel.system_info";
    definition.displayName = "System Info";
    definition.category = "Utility";
    definition.createInstance = &CreatePanel;
    definition.destroyInstance = &DestroyPanel;
    definition.render = &RenderPanel;
    return api->register_panel(api->userData, &definition);
}
