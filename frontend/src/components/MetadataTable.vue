<template>
  <div class="space-y-4">
    <template v-if="fileType === 'document'">
      <div class="card p-4">
        <div v-if="documentMetaRows.length" class="grid gap-6 sm:grid-cols-[1fr_1.5fr] items-start">
          <div>
            <h4 class="font-polonium text-xl font-bold text-gray-900 mb-3">О документе</h4>
            <div
              v-for="(row, idx) in documentMetaRowsText"
              :key="`doc-meta-t-${idx}`"
              class="flex flex-col gap-1 py-2"
            >
              <div class="text-sm font-medium text-gray-600">{{ row.key }}</div>
              <div class="break-words text-sm font-mono text-gray-900">{{ row.value }}</div>
            </div>
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            <div
              v-for="(row, idx) in documentMetaRowsDates"
              :key="`doc-meta-d-${idx}`"
              class="flex flex-col gap-2"
            >
              <div class="text-sm font-medium text-gray-600">{{ row.key }}</div>
              <div class="flex flex-col gap-2">
                <div v-if="getCalendarMonth(row.value)" class="inline-flex w-fit max-w-[280px] flex-col rounded-lg border border-gray-200 bg-white p-3">
                  <div class="mb-2 text-center text-sm font-medium text-gray-700">
                    {{ getCalendarMonth(row.value).monthName }} {{ getCalendarMonth(row.value).year }}
                  </div>
                  <div class="grid grid-cols-7 gap-px text-center text-xs">
                    <div v-for="w in 7" :key="`wd-${w}`" class="py-1 font-medium text-gray-500">
                      {{ ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][w - 1] }}
                    </div>
                    <template v-for="(week, wi) in getCalendarMonth(row.value).weeks" :key="`w-${wi}`">
                      <div
                        v-for="(day, di) in week"
                        :key="`d-${wi}-${di}`"
                        class="flex h-8 w-8 items-center justify-center rounded text-xs"
                        :class="day === getCalendarMonth(row.value).highlightDay ? 'bg-[#212121] text-[#FFF5E5] font-semibold' : day ? 'text-gray-700' : 'text-gray-300'"
                      >
                        {{ day || '' }}
                      </div>
                    </template>
                  </div>
                  <div class="mt-2 text-center text-sm text-gray-500">{{ daysAgoLabel(row.value) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <p v-else class="mt-3 text-sm text-gray-500">Свойства не найдены.</p>
      </div>

      <template v-if="!showOnlyDocumentMeta">
        <div class="card p-4">
          <h4 class="font-polonium text-xl font-bold text-gray-900">Изображения в документе</h4>
          <p class="mt-1 text-sm text-gray-500">
            Всего: {{ metadata.images_count || 0 }}, с признаками ИИ: {{ metadata.images_with_ai_count || 0 }}
          </p>
        </div>

        <div v-if="(metadata.images || []).length === 0" class="card p-4 text-sm text-gray-500">
          В документе нет извлечённых изображений.
        </div>

        <div
          v-for="(img, index) in (metadata.images || [])"
          :key="`doc-image-${index}`"
          class="card p-4"
        >
          <div class="flex flex-wrap items-center justify-between gap-2">
            <p class="font-medium text-gray-900 break-words">{{ index + 1 }}. {{ img.filename || 'Без имени' }}</p>
            <div class="flex items-center gap-2">
              <span :class="['status-chip', aiChipClass((img.ai_indicators && img.ai_indicators.ai_probability) ?? 0)]">ИИ: {{ (img.ai_indicators && img.ai_indicators.ai_probability) ?? 0 }}%</span>
              <button type="button" class="secondary-btn px-2 py-1 text-xs" @click="toggleImageExpanded(index)">
                {{ isImageExpanded(index) ? 'Скрыть' : 'Подробнее' }}
              </button>
            </div>
          </div>
          <p v-if="img.archive_path" class="mt-1 text-xs text-gray-500">Путь: {{ img.archive_path }}</p>
          <p v-if="img.size" class="text-xs text-gray-500">Размер: {{ formatFileSize(img.size) }}</p>
          <p v-if="img.ai_indicators && img.ai_indicators.software_detected && img.ai_indicators.software_detected.length" class="text-sm text-gray-600">
            ПО: {{ img.ai_indicators.software_detected.join(', ') }}
          </p>
          <ul v-if="img.ai_indicators && img.ai_indicators.anomalies && img.ai_indicators.anomalies.length" class="mt-1 list-disc list-inside text-sm text-gray-600">
            <li v-for="(anom, ai) in img.ai_indicators.anomalies" :key="ai">{{ anom }}</li>
          </ul>

          <div v-if="isImageExpanded(index)" class="mt-4 space-y-3 border-t border-gray-200 pt-4">
            <h5 class="font-polonium text-lg font-bold text-gray-700">Метаданные изображения</h5>
            <div v-if="buildImageSections(img.metadata).length === 0" class="text-sm text-gray-500">
              Нет детальных метаданных.
            </div>
            <div
              v-for="section in buildImageSections(img.metadata)"
              :key="`${section.title}-${index}`"
              class="rounded-lg border border-gray-200 bg-gray-50 overflow-hidden"
            >
              <div class="border-b border-gray-200 bg-gray-100 px-3 py-2">
                <h6 class="font-polonium text-xl font-bold text-gray-900">{{ section.title }}</h6>
              </div>
              <div v-if="section.rows.length > 0" class="divide-y divide-gray-200">
                <div
                  v-for="(row, rowIdx) in section.rows"
                  :key="`${section.title}-${index}-${rowIdx}`"
                  class="grid gap-2 px-3 py-2 sm:grid-cols-[180px_1fr]"
                >
                  <div class="text-sm font-medium text-gray-600">{{ row.key }}</div>
                  <div class="break-words text-sm font-mono text-gray-900">{{ row.value }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>
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
    },
    showOnlyDocumentMeta: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      expandedImageIndexes: []
    }
  },
  computed: {
    documentTypeLabel() {
      if (this.metadata?.document_type === 'powerpoint') return 'PowerPoint'
      if (this.metadata?.document_type === 'word') return 'Word'
      return 'Офисный документ'
    },
    documentMetaRows() {
      if (this.fileType !== 'document') return []
      const source = this.metadata?.document_metadata
      if (!source || typeof source !== 'object') return []

      const map = [
        ['creator', 'Автор'],
        ['last_modified_by', 'Последний редактор'],
        ['created', 'Создан'],
        ['modified', 'Изменен']
      ]

      return map
        .filter(([key]) => this.hasValue(source[key]))
        .map(([key, label]) => ({ rawKey: key, key: label, value: source[key] }))
    },
    documentMetaRowsText() {
      return this.documentMetaRows.filter(
        (row) => row.rawKey !== 'created' && row.rawKey !== 'modified'
      )
    },
    documentMetaRowsDates() {
      return this.documentMetaRows.filter(
        (row) => row.rawKey === 'created' || row.rawKey === 'modified'
      )
    },
    groupedMetadata() {
      return this.getGroupedMetadata(this.metadata)
    },
    sections() {
      if (this.fileType === 'video') {
        return [
          this.buildSection('Метаданные контейнера', this.metadata.container),
          this.buildSection('Видео поток', this.metadata.video_stream),
          this.buildSection('Аудио поток', this.metadata.audio_stream),
          this.buildSection('Информация о кодировании', this.metadata.encoding_info),
        ].filter(Boolean)
      }

      if (this.fileType === 'image' && this.groupedMetadata) {
        return Object.entries(this.groupedMetadata).map(([sectionName, sectionData]) => {
          const rows = sectionData.map((item) => ({
            key: this.formatGroupedKey(item),
            value: this.formatGroupedValue(item),
          }))
          return { title: sectionName, rows }
        })
      }

      if (this.fileType === 'image') {
        return [
          this.buildSection('EXIF данные', this.filteredExifData),
          this.buildSection('XMP данные', this.filteredXmpData),
          this.buildSection('Характеристики изображения', this.filteredImageCharacteristics),
        ].filter(Boolean)
      }

      return []
    },
    filteredExifData() {
      return this.filterObject(this.metadata.exif, (key, value) => key !== 'error' && !key.startsWith('_') && this.hasValue(value))
    },
    filteredXmpData() {
      return this.filterObject(this.metadata.xmp, (key, value) => key !== 'error' && this.hasValue(value))
    },
    filteredImageCharacteristics() {
      const excludeKeys = ['suspicious_features', 'error']
      return this.filterObject(this.metadata.image_characteristics, (key, value) => !excludeKeys.includes(key) && this.hasValue(value))
    }
  },
  methods: {
    isImageExpanded(index) {
      return this.expandedImageIndexes.includes(index)
    },
    toggleImageExpanded(index) {
      if (this.isImageExpanded(index)) {
        this.expandedImageIndexes = this.expandedImageIndexes.filter((item) => item !== index)
        return
      }
      this.expandedImageIndexes = [...this.expandedImageIndexes, index]
    },
    getGroupedMetadata(sourceMetadata) {
      if (!sourceMetadata || !sourceMetadata.exif || !sourceMetadata.exif._grouped_metadata) return null
      const grouped = sourceMetadata.exif._grouped_metadata
      if (typeof grouped !== 'object' || grouped === null) return null

      const filtered = {}
      for (const [sectionName, sectionData] of Object.entries(grouped)) {
        if (Array.isArray(sectionData) && sectionData.length > 0) {
          filtered[sectionName] = sectionData
        }
      }
      return Object.keys(filtered).length ? filtered : null
    },
    buildImageSections(imageMetadata) {
      if (!imageMetadata || typeof imageMetadata !== 'object') return []

      const grouped = this.getGroupedMetadata(imageMetadata)
      if (grouped) {
        return Object.entries(grouped).map(([sectionName, sectionData]) => {
          const rows = sectionData.map((item) => ({
            key: this.formatGroupedKey(item),
            value: this.formatGroupedValue(item)
          }))
          return { title: sectionName, rows }
        })
      }

      const filteredExif = this.filterObject(
        imageMetadata.exif,
        (key, value) => key !== 'error' && !key.startsWith('_') && this.hasValue(value)
      )
      const filteredXmp = this.filterObject(
        imageMetadata.xmp,
        (key, value) => key !== 'error' && this.hasValue(value)
      )
      const filteredCharacteristics = this.filterObject(
        imageMetadata.image_characteristics,
        (key, value) => !['suspicious_features', 'error'].includes(key) && this.hasValue(value)
      )

      return [
        this.buildSection('EXIF данные', filteredExif),
        this.buildSection('XMP данные', filteredXmp),
        this.buildSection('Характеристики изображения', filteredCharacteristics)
      ].filter(Boolean)
    },
    aiChipClass(pct) {
      const n = Number(pct)
      if (n < 35) return 'status-chip-ai-low'
      if (n <= 70) return 'status-chip-ai-mid'
      return 'status-chip-ai-high'
    },
    formatFileSize(bytes) {
      if (typeof bytes !== 'number' || bytes <= 0) return 'N/A'
      const units = ['B', 'KB', 'MB', 'GB']
      let size = bytes
      let index = 0
      while (size >= 1024 && index < units.length - 1) {
        size /= 1024
        index += 1
      }
      return `${size.toFixed(index === 0 ? 0 : 2)} ${units[index]}`
    },
    buildSection(title, source) {
      if (!source || typeof source !== 'object') return null
      const rows = Object.entries(source).map(([key, value]) => ({
        key: this.formatKey(key),
        value: this.formatValue(value, key)
      }))
      return { title, rows }
    },
    filterObject(obj, predicate) {
      if (!obj || typeof obj !== 'object') return {}
      const filtered = {}
      for (const [key, value] of Object.entries(obj)) {
        if (predicate(key, value)) {
          filtered[key] = value
        }
      }
      return filtered
    },
    hasValue(value) {
      return value !== null && value !== undefined && value !== ''
    },
    formatKey(key) {
      let formatted = String(key)
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .replace(/\s+/g, ' ')
        .trim()

      if (formatted.length > 0) {
        formatted = formatted.charAt(0).toUpperCase() + formatted.slice(1)
      }
      return formatted
    },
    formatGroupedKey(item) {
      let rawKey = ''
      if (Array.isArray(item) && item.length >= 2) {
        rawKey = item[0]
      } else if (typeof item === 'object' && item !== null) {
        const keys = Object.keys(item)
        if (keys.length > 0) rawKey = keys[0]
      }
      if (typeof rawKey === 'string' && rawKey.includes(':')) {
        rawKey = rawKey.split(':').pop().trim() || rawKey
      }
      return this.formatKey(rawKey || 'Параметр')
    },
    formatGroupedValue(item) {
      if (Array.isArray(item) && item.length >= 2) {
        return this.formatValue(item[1], item[0])
      }
      if (typeof item === 'object' && item !== null) {
        const keys = Object.keys(item)
        if (keys.length > 0) {
          const key = keys[0]
          return this.formatValue(item[key], key)
        }
      }
      return 'N/A'
    },
    getCalendarMonth(isoString) {
      if (!isoString || typeof isoString !== 'string') return null
      const d = new Date(isoString)
      if (Number.isNaN(d.getTime())) return null
      const year = d.getFullYear()
      const month = d.getMonth()
      const dayOfDate = d.getDate()
      const first = new Date(year, month, 1)
      const last = new Date(year, month + 1, 0)
      const daysInMonth = last.getDate()
      const monthNames = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
      const firstWeekday = (first.getDay() + 6) % 7
      const cells = []
      for (let i = 0; i < 42; i++) {
        if (i < firstWeekday || i >= firstWeekday + daysInMonth) cells.push(null)
        else cells.push(i - firstWeekday + 1)
      }
      const weeks = []
      for (let r = 0; r < 6; r++) weeks.push(cells.slice(r * 7, (r + 1) * 7))
      return { monthName: monthNames[month], year, weeks, highlightDay: dayOfDate }
    },
    formatCalendarDate(isoString) {
      if (!isoString || typeof isoString !== 'string') return '—'
      const d = new Date(isoString)
      if (Number.isNaN(d.getTime())) return isoString
      const day = String(d.getDate()).padStart(2, '0')
      const month = String(d.getMonth() + 1).padStart(2, '0')
      const year = d.getFullYear()
      return `${day}.${month}.${year}`
    },
    daysAgoLabel(isoString) {
      if (!isoString || typeof isoString !== 'string') return ''
      const d = new Date(isoString)
      if (Number.isNaN(d.getTime())) return ''
      const now = new Date()
      const diffMs = now - d
      const days = Math.floor(diffMs / (24 * 60 * 60 * 1000))
      if (days < 0) return 'через ' + this.pluralDays(Math.abs(days))
      if (days === 0) return 'сегодня'
      return this.pluralDays(days) + ' назад'
    },
    pluralDays(n) {
      const mod10 = n % 10
      const mod100 = n % 100
      if (mod10 === 1 && mod100 !== 11) return n + ' день'
      if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return n + ' дня'
      return n + ' дней'
    },
    formatValue(value, key) {
      if (value === null || value === undefined) return 'N/A'

      if (Array.isArray(value)) {
        return value.map((v) => this.formatValue(v, key)).join(', ')
      }

      if (typeof value === 'object') {
        const json = JSON.stringify(value)
        return json.length > 300 ? json.substring(0, 300) + '...' : json
      }

      if (key === 'duration' && typeof value === 'string') {
        const seconds = parseFloat(value)
        if (!Number.isNaN(seconds)) {
          const minutes = Math.floor(seconds / 60)
          const secs = Math.floor(seconds % 60)
          return `${minutes}:${secs.toString().padStart(2, '0')}`
        }
      }

      if (key === 'bit_rate' && typeof value === 'string') {
        const bits = parseInt(value, 10)
        if (!Number.isNaN(bits)) {
          if (bits >= 1000000) return `${(bits / 1000000).toFixed(2)} Mbps`
          if (bits >= 1000) return `${(bits / 1000).toFixed(2)} Kbps`
          return `${bits} bps`
        }
      }

      const text = String(value)
      return text.length > 500 ? text.substring(0, 500) + '...' : text
    }
  }
}
</script>
