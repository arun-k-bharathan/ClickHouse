#include <Storages/NamedCollectionConfiguration.h>
#include <Poco/Util/XMLConfiguration.h>
#include <Common/Exception.h>
#include <Common/SettingsChanges.h>
#include <Common/FieldVisitorToString.h>

namespace DB
{

namespace ErrorCodes
{
    extern const int BAD_ARGUMENTS;
    extern const int NOT_IMPLEMENTED;
}

namespace NamedCollectionConfiguration
{

template <typename T> T getConfigValue(
    const Poco::Util::AbstractConfiguration & config,
    const std::string & path)
{
    return getConfigValueOrDefault<T>(config, path);
}

template <typename T> T getConfigValueOrDefault(
    const Poco::Util::AbstractConfiguration & config,
    const std::string & path,
    const T * default_value)
{
    if (!config.has(path))
    {
        if (!default_value)
            throw Exception(ErrorCodes::BAD_ARGUMENTS, "No such key `{}`", path);
        return *default_value;
    }

    if constexpr (std::is_same_v<T, String>)
        return config.getString(path);
    else if constexpr (std::is_same_v<T, UInt64>)
        return config.getUInt64(path);
    else if constexpr (std::is_same_v<T, Int64>)
        return config.getInt64(path);
    else if constexpr (std::is_same_v<T, Float64>)
        return config.getDouble(path);
    else
        throw Exception(
            ErrorCodes::NOT_IMPLEMENTED,
            "Unsupported type in getConfigValueOrDefault(). "
            "Supported types are String, UInt64, Int64, Float64");
}

template<typename T> void setConfigValue(
    Poco::Util::AbstractConfiguration & config,
    const std::string & path,
    const T & value,
    bool update)
{
    if (!update && config.has(path))
        throw Exception(ErrorCodes::BAD_ARGUMENTS, "Key `{}` already exists", path);

    if constexpr (std::is_same_v<T, String>)
        config.setString(path, value);
    else if constexpr (std::is_same_v<T, UInt64>)
        config.setUInt64(path, value);
    else if constexpr (std::is_same_v<T, Int64>)
        config.setInt64(path, value);
    else if constexpr (std::is_same_v<T, Float64>)
        config.setDouble(path, value);
    else
        throw Exception(
            ErrorCodes::NOT_IMPLEMENTED,
            "Unsupported type in setConfigValue(). "
            "Supported types are String, UInt64, Int64, Float64");
}

template <typename T> void copyConfigValue(
    const Poco::Util::AbstractConfiguration & from_config,
    const std::string & from_path,
    Poco::Util::AbstractConfiguration & to_config,
    const std::string & to_path)
{
    if (!from_config.has(from_path))
        throw Exception(ErrorCodes::BAD_ARGUMENTS, "No such key `{}`", from_path);

    if (to_config.has(to_path))
        throw Exception(ErrorCodes::BAD_ARGUMENTS, "Key `{}` already exists", to_path);

    if constexpr (std::is_same_v<T, String>)
        to_config.setString(to_path, from_config.getString(from_path));
    else if constexpr (std::is_same_v<T, UInt64>)
        to_config.setUInt64(to_path, from_config.getUInt64(from_path));
    else if constexpr (std::is_same_v<T, Int64>)
        to_config.setInt64(to_path, from_config.getInt64(from_path));
    else if constexpr (std::is_same_v<T, Float64>)
        to_config.setDouble(to_path, from_config.getDouble(from_path));
    else
        throw Exception(
            ErrorCodes::NOT_IMPLEMENTED,
            "Unsupported type in copyConfigValue(). "
            "Supported types are String, UInt64, Int64, Float64");
}

void removeConfigValue(
    Poco::Util::AbstractConfiguration & config,
    const std::string & path)
{
    if (!config.has(path))
        throw Exception(ErrorCodes::BAD_ARGUMENTS, "No such key `{}`", path);
    config.remove(path);
}

ConfigurationPtr createEmptyConfiguration(const std::string & root_name)
{
    using DocumentPtr = Poco::AutoPtr<Poco::XML::Document>;
    using ElementPtr = Poco::AutoPtr<Poco::XML::Element>;

    DocumentPtr xml_document(new Poco::XML::Document());
    ElementPtr root_element(xml_document->createElement(root_name));
    xml_document->appendChild(root_element);

    ConfigurationPtr config(new Poco::Util::XMLConfiguration(xml_document));
    return config;
}

ConfigurationPtr createConfiguration(const std::string & root_name, const SettingsChanges & settings)
{
    namespace Configuration = NamedCollectionConfiguration;

    auto config = Configuration::createEmptyConfiguration(root_name);
    for (const auto & [name, value] : settings)
        Configuration::setConfigValue<String>(*config, name, convertFieldToString(value));

    return config;
}

template String getConfigValue<String>(const Poco::Util::AbstractConfiguration & config,
                                       const std::string & path);
template UInt64 getConfigValue<UInt64>(const Poco::Util::AbstractConfiguration & config,
                                       const std::string & path);
template Int64 getConfigValue<Int64>(const Poco::Util::AbstractConfiguration & config,
                                     const std::string & path);
template Float64 getConfigValue<Float64>(const Poco::Util::AbstractConfiguration & config,
                                         const std::string & path);

template String getConfigValueOrDefault<String>(const Poco::Util::AbstractConfiguration & config,
                                                const std::string & path, const String * default_value);
template UInt64 getConfigValueOrDefault<UInt64>(const Poco::Util::AbstractConfiguration & config,
                                                const std::string & path, const UInt64 * default_value);
template Int64 getConfigValueOrDefault<Int64>(const Poco::Util::AbstractConfiguration & config,
                                              const std::string & path, const Int64 * default_value);
template Float64 getConfigValueOrDefault<Float64>(const Poco::Util::AbstractConfiguration & config,
                                                  const std::string & path, const Float64 * default_value);

template void setConfigValue<String>(Poco::Util::AbstractConfiguration & config,
                                     const std::string & path, const String & value, bool update);
template void setConfigValue<UInt64>(Poco::Util::AbstractConfiguration & config,
                                     const std::string & path, const UInt64 & value, bool update);
template void setConfigValue<Int64>(Poco::Util::AbstractConfiguration & config,
                                    const std::string & path, const Int64 & value, bool update);
template void setConfigValue<Float64>(Poco::Util::AbstractConfiguration & config,
                                      const std::string & path, const Float64 & value, bool update);

template void copyConfigValue<String>(const Poco::Util::AbstractConfiguration & from_config, const std::string & from_path,
                                      Poco::Util::AbstractConfiguration & to_config, const std::string & to_path);
template void copyConfigValue<UInt64>(const Poco::Util::AbstractConfiguration & from_config, const std::string & from_path,
                                      Poco::Util::AbstractConfiguration & to_config, const std::string & to_path);
template void copyConfigValue<Int64>(const Poco::Util::AbstractConfiguration & from_config, const std::string & from_path,
                                     Poco::Util::AbstractConfiguration & to_config, const std::string & to_path);
template void copyConfigValue<Float64>(const Poco::Util::AbstractConfiguration & from_config, const std::string & from_path,
                                       Poco::Util::AbstractConfiguration & to_config, const std::string & to_path);
}

}
