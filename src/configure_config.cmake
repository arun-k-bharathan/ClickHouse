if (TARGET ch_contrib::rocksdb)
    set(USE_ROCKSDB 1)
endif()
if (TARGET ch_contrib::bzip2)
    set(USE_BZIP2 1)
endif()
if (TARGET ch_contrib::snappy)
    set(USE_SNAPPY 1)
endif()
if (TARGET ch_contrib::brotli)
    set(USE_BROTLI 1)
endif()
if (TARGET ch_contrib::hivemetastore)
    set(USE_HIVE 1)
endif()
if (TARGET ch_contrib::rdkafka)
    set(USE_RDKAFKA 1)
endif()
if (TARGET OpenSSL::SSL)
    set(USE_SSL 1)
endif()
if (TARGET ch_contrib::ldap)
    set(USE_LDAP 1)
endif()
if (TARGET ch_contrib::grpc)
    set(USE_GRPC 1)
endif()
if (TARGET ch_contrib::hdfs)
    set(USE_HDFS 1)
endif()
if (TARGET ch_contrib::nuraft)
    set(USE_NURAFT 1)
endif()
if (TARGET ch_contrib::icu)
    set(USE_ICU 1)
endif()
if (TARGET ch_contrib::simdjson)
    set(USE_SIMDJSON 1)
endif()
if (TARGET ch_contrib::rapidjson)
    set(USE_RAPIDJSON 1)
endif()
if (TARGET ch_contrib::azure_sdk)
    set(USE_AZURE_BLOB_STORAGE 1)
endif()
