<template>
  <div class="space-y-6">
    <!-- Группированные метаданные (если доступны) -->
    <div v-if="hasGroupedMetadata" class="space-y-6">
      <div 
        v-for="(sectionData, sectionName) in groupedMetadata" 
        :key="sectionName"
        class="border-2 border-black overflow-hidden"
      >
        <div class="border-b-2 border-black px-5 py-3 bg-white">
          <h4 class="font-bold text-black text-sm uppercase tracking-wide">
            {{ sectionName }}
          </h4>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full">
            <tbody class="bg-white">
              <tr 
                v-for="(item, index) in sectionData" 
                :key="`${sectionName}-${index}`"
                class="border-b-2 border-black last:border-b-0"
              >
                <td class="px-5 py-3 whitespace-nowrap text-xs font-medium text-black w-1/3 border-r-2 border-black">
                  {{ formatGroupedKey(item) }}
                </td>
                <td class="px-5 py-3 text-xs text-black break-words">
                  <span class="font-mono">{{ formatGroupedValue(item) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Старый формат (fallback) -->
    <template v-else>
      <!-- EXIF данные для изображений -->
      <div v-if="fileType === 'image'" class="border-2 border-black overflow-hidden">
        <div class="border-b-2 border-black px-5 py-3 bg-white">
          <h4 class="font-bold text-black text-sm uppercase tracking-wide">EXIF данные</h4>
        </div>
        <div v-if="hasExifData" class="overflow-x-auto">
          <table class="min-w-full">
            <tbody class="bg-white">
              <tr v-for="(value, key) in filteredExifData" :key="key" class="border-b-2 border-black last:border-b-0">
                <td class="px-5 py-3 whitespace-nowrap text-xs font-medium text-black w-1/3 border-r-2 border-black">
                  {{ formatKey(key) }}
                </td>
                <td class="px-5 py-3 text-xs text-black">
                  <span class="font-mono">{{ formatValue(value, key) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="px-6 py-10 text-center bg-white border-t-2 border-black">
          <p class="text-sm text-black mb-1">EXIF метаданные отсутствуют</p>
          <p class="text-xs text-gray-600">Это может указывать на то, что изображение было обработано или создано с помощью ИИ</p>
        </div>
      </div>

      <!-- XMP данные для изображений -->
      <div v-if="fileType === 'image'" class="border-2 border-black overflow-hidden">
        <div class="border-b-2 border-black px-5 py-3 bg-white">
          <h4 class="font-bold text-black text-sm uppercase tracking-wide">XMP данные</h4>
        </div>
        <div v-if="hasXmpData" class="overflow-x-auto">
          <table class="min-w-full">
            <tbody class="bg-white">
              <tr v-for="(value, key) in filteredXmpData" :key="key" class="border-b-2 border-black last:border-b-0">
                <td class="px-5 py-3 whitespace-nowrap text-xs font-medium text-black w-1/3 border-r-2 border-black">
                  {{ formatKey(key) }}
                </td>
                <td class="px-5 py-3 text-xs text-black break-words">
                  <span class="font-mono">{{ formatValue(value, key) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="px-6 py-10 text-center bg-white border-t-2 border-black">
          <p class="text-sm text-black mb-1">XMP метаданные отсутствуют</p>
          <p class="text-xs text-gray-600">XMP данные обычно содержат информацию о редактировании изображения</p>
        </div>
      </div>
    </template>

    <!-- Метаданные контейнера для видео -->
    <div v-if="fileType === 'video' && metadata.container" class="border-2 border-black overflow-hidden mb-6">
      <div class="border-b-2 border-black px-5 py-3 bg-white">
        <h4 class="font-bold text-black text-sm uppercase tracking-wide">Метаданные контейнера</h4>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full">
            <tbody class="bg-white">
              <tr v-for="(value, key) in metadata.container" :key="key" v-if="value" class="border-b-2 border-black last:border-b-0">
                <td class="px-5 py-3 whitespace-nowrap text-xs font-medium text-black w-1/3 border-r-2 border-black">
                  {{ formatKey(key) }}
                </td>
                <td class="px-5 py-3 text-xs text-black">
                  <span class="font-mono">{{ formatValue(value, key) }}</span>
                </td>
              </tr>
            </tbody>
        </table>
      </div>
    </div>

    <!-- Видео поток -->
    <div v-if="fileType === 'video' && metadata.video_stream" class="border-2 border-black overflow-hidden mb-6">
      <div class="border-b-2 border-black px-5 py-3 bg-white">
        <h4 class="font-bold text-black text-sm uppercase tracking-wide">Видео поток</h4>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full">
            <tbody class="bg-white">
              <tr v-for="(value, key) in metadata.video_stream" :key="key" v-if="value" class="border-b-2 border-black last:border-b-0">
                <td class="px-5 py-3 whitespace-nowrap text-xs font-medium text-black w-1/3 border-r-2 border-black">
                  {{ formatKey(key) }}
                </td>
                <td class="px-5 py-3 text-xs text-black">
                  <span class="font-mono">{{ formatValue(value, key) }}</span>
                </td>
              </tr>
            </tbody>
        </table>
      </div>
    </div>

    <!-- Аудио поток -->
    <div v-if="fileType === 'video' && metadata.audio_stream" class="border-2 border-black overflow-hidden mb-6">
      <div class="border-b-2 border-black px-5 py-3 bg-white">
        <h4 class="font-bold text-black text-sm uppercase tracking-wide">Аудио поток</h4>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full">
            <tbody class="bg-white">
              <tr v-for="(value, key) in metadata.audio_stream" :key="key" v-if="value" class="border-b-2 border-black last:border-b-0">
                <td class="px-5 py-3 whitespace-nowrap text-xs font-medium text-black w-1/3 border-r-2 border-black">
                  {{ formatKey(key) }}
                </td>
                <td class="px-5 py-3 text-xs text-black">
                  <span class="font-mono">{{ formatValue(value, key) }}</span>
                </td>
              </tr>
            </tbody>
        </table>
      </div>
    </div>

    <!-- Информация о кодировании для видео -->
    <div v-if="fileType === 'video' && metadata.encoding_info" class="border-2 border-black overflow-hidden mb-6">
      <div class="border-b-2 border-black px-5 py-3 bg-white">
        <h4 class="font-bold text-black text-sm uppercase tracking-wide">Информация о кодировании</h4>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full">
            <tbody class="bg-white">
              <tr v-for="(value, key) in metadata.encoding_info" :key="key" class="border-b-2 border-black last:border-b-0">
                <td class="px-5 py-3 whitespace-nowrap text-xs font-medium text-black w-1/3 border-r-2 border-black">
                  {{ formatKey(key) }}
                </td>
                <td class="px-5 py-3 text-xs text-black" :class="getSuspiciousClass(key, value)">
                  <span class="font-mono">{{ formatValue(value, key) }}</span>
                </td>
              </tr>
            </tbody>
        </table>
      </div>
    </div>

    <!-- Характеристики изображения -->
    <div v-if="fileType === 'image' && metadata.image_characteristics" class="border-2 border-black overflow-hidden mb-6">
      <div class="border-b-2 border-black px-5 py-3 bg-white">
        <h4 class="font-bold text-black text-sm uppercase tracking-wide">Характеристики изображения</h4>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full">
            <tbody class="bg-white">
              <tr v-for="(value, key) in filteredImageCharacteristics" :key="key" class="border-b-2 border-black last:border-b-0">
                <td class="px-5 py-3 whitespace-nowrap text-xs font-medium text-black w-1/3 border-r-2 border-black">
                  {{ formatKey(key) }}
                </td>
                <td class="px-5 py-3 text-xs text-black" :class="getImageCharClass(key, value)">
                  <span class="font-mono">{{ formatImageCharValue(value, key) }}</span>
                </td>
              </tr>
            </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MetadataTable',
  props: {
    metadata: {
      type: Object,
      required: true
    },
    fileType: {
      type: String,
      required: true
    }
  },
  computed: {
    groupedMetadata() {
      // Проверяем наличие сгруппированных метаданных из exiftool
      if (this.metadata.exif && this.metadata.exif._grouped_metadata) {
        const grouped = this.metadata.exif._grouped_metadata
        // Проверяем, что это объект и в нем есть данные
        if (typeof grouped === 'object' && grouped !== null) {
          // Фильтруем только секции с данными
          const filtered = {}
          for (const [sectionName, sectionData] of Object.entries(grouped)) {
            // Проверяем, что это массив и в нем есть элементы
            if (Array.isArray(sectionData) && sectionData.length > 0) {
              filtered[sectionName] = sectionData
            }
          }
          const result = Object.keys(filtered).length > 0 ? filtered : null
          return result
        }
      }
      return null
    },
    hasGroupedMetadata() {
      const grouped = this.groupedMetadata
      return grouped !== null && grouped !== undefined && Object.keys(grouped).length > 0
    },
    filteredExifData() {
      if (!this.metadata.exif) return {}
      const filtered = {}
      for (const [key, value] of Object.entries(this.metadata.exif)) {
        // Пропускаем служебные поля
        if (key !== 'error' && !key.startsWith('_') && value !== null && value !== undefined && value !== '') {
          filtered[key] = value
        }
      }
      return filtered
    },
    hasExifData() {
      return Object.keys(this.filteredExifData).length > 0
    },
    filteredXmpData() {
      if (!this.metadata.xmp) return {}
      const filtered = {}
      for (const [key, value] of Object.entries(this.metadata.xmp)) {
        if (key !== 'error' && value !== null && value !== undefined && value !== '') {
          filtered[key] = value
        }
      }
      return filtered
    },
    hasXmpData() {
      return Object.keys(this.filteredXmpData).length > 0
    },
    filteredImageCharacteristics() {
      if (!this.metadata.image_characteristics) return {}
      const filtered = {}
      const excludeKeys = ['suspicious_features', 'error']
      for (const [key, value] of Object.entries(this.metadata.image_characteristics)) {
        if (!excludeKeys.includes(key) && value !== null && value !== undefined) {
          filtered[key] = value
        }
      }
      return filtered
    }
  },
  methods: {
    formatKey(key) {
      // Преобразование различных форматов ключей в читаемый формат
      let formatted = key
        // Заменяем подчеркивания на пробелы
        .replace(/_/g, ' ')
        // Добавляем пробелы перед заглавными буквами
        .replace(/([A-Z])/g, ' $1')
        // Убираем лишние пробелы
        .replace(/\s+/g, ' ')
        .trim()
      
      // Капитализируем первую букву
      if (formatted.length > 0) {
        formatted = formatted.charAt(0).toUpperCase() + formatted.slice(1)
      }
      
      return formatted
    },
    
    formatGroupedKey(item) {
      // Обработка группированных данных (массив [key, value] или объект)
      let rawKey = ''
      if (Array.isArray(item) && item.length >= 2) {
        rawKey = item[0]
      } else if (typeof item === 'object' && item !== null) {
        const keys = Object.keys(item)
        if (keys.length > 0) rawKey = keys[0]
      } else {
        return String(item)
      }
      // Показываем только имя тега (после последнего ":"), чтобы не дублировать имя секции
      if (typeof rawKey === 'string' && rawKey.includes(':')) {
        rawKey = rawKey.split(':').pop().trim() || rawKey
      }
      return this.formatKey(rawKey)
    },
    
    formatGroupedValue(item) {
      // Обработка группированных данных (массив [key, value] или объект)
      let key, value
      
      if (Array.isArray(item) && item.length >= 2) {
        key = item[0]
        value = item[1]
      } else if (typeof item === 'object' && item !== null) {
        const keys = Object.keys(item)
        if (keys.length > 0) {
          key = keys[0]
          value = item[key]
        }
      } else {
        return String(item)
      }
      
      return this.formatValue(value, key)
    },
    
    formatValue(value, key) {
      if (value === null || value === undefined) {
        return 'N/A'
      }
      
      // Обработка массивов
      if (Array.isArray(value)) {
        return value.map(v => this.formatValue(v, key)).join(', ')
      }
      
      if (typeof value === 'object') {
        // Для объектов показываем JSON, но ограничиваем длину
        const jsonStr = JSON.stringify(value, null, 2)
        if (jsonStr.length > 200) {
          return jsonStr.substring(0, 200) + '...'
        }
        return jsonStr
      }
      
      const valueStr = String(value)
      
      // Обработка бинарных данных
      if (valueStr.includes('Binary data') || valueStr.includes('bytes')) {
        return valueStr
      }
      
      // Форматирование специальных значений
      if (key === 'duration' && typeof value === 'string') {
        const seconds = parseFloat(value)
        if (!isNaN(seconds)) {
          const minutes = Math.floor(seconds / 60)
          const secs = Math.floor(seconds % 60)
          return `${minutes}:${secs.toString().padStart(2, '0')}`
        }
      }
      
      if (key === 'bit_rate' && typeof value === 'string') {
        const bits = parseInt(value)
        if (!isNaN(bits)) {
          if (bits >= 1000000) {
            return `${(bits / 1000000).toFixed(2)} Mbps`
          } else if (bits >= 1000) {
            return `${(bits / 1000).toFixed(2)} Kbps`
          }
          return `${bits} bps`
        }
      }
      
      // Ограничение длины длинных строк
      if (valueStr.length > 500) {
        return valueStr.substring(0, 500) + '...'
      }
      
      return valueStr
    },
    
    getSuspiciousClass(key, value) {
      // Выделение подозрительных полей
      if (key === 'suspicious' && value === true) {
        return 'font-semibold'
      }
      if (key === 'ai_indicators' && Array.isArray(value) && value.length > 0) {
        return 'font-semibold'
      }
      return ''
    },
    
    formatImageCharValue(value, key) {
      if (value === null || value === undefined) {
        return 'N/A'
      }
      
      // Булевы значения
      if (typeof value === 'boolean') {
        return value ? 'Да' : 'Нет'
      }
      
      // Размеры изображения
      if (key === 'width' || key === 'height') {
        return `${value} px`
      }
      
      // Соотношение сторон
      if (key === 'aspect_ratio') {
        return value.toFixed(2)
      }
      
      return String(value)
    },
    
    getImageCharClass(key, value) {
      // Выделение подозрительных характеристик
      if (key === 'is_square' && value === true) {
        return 'font-medium'
      }
      if (key === 'is_standard_ai_size' && value === true) {
        return 'font-semibold'
      }
      return ''
    }
  }
}
</script>
