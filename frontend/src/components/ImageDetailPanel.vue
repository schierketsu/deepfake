<template>
  <div class="space-y-4">
    <div class="card card-no-border p-4">
      <p v-if="softwareDetected" class="text-sm text-gray-600">ПО: {{ softwareDetected }}</p>
      <ul v-if="anomalies.length" class="mt-1 list-disc list-inside text-sm text-gray-600">
        <li v-for="(anom, ai) in anomalies" :key="ai">{{ anom }}</li>
      </ul>
    </div>

    <div class="card p-4">
      <h5 class="font-polonium text-xl font-bold text-gray-900">Метаданные изображения</h5>
      <div v-if="imageSections.length === 0" class="mt-3 text-sm text-gray-500">
        Нет детальных метаданных.
      </div>
      <div
        v-for="section in imageSections"
        :key="section.title"
        class="mt-3 rounded-lg border border-gray-200 bg-gray-50 overflow-hidden first:mt-0"
      >
        <div class="border-b border-gray-200 bg-gray-100 px-3 py-2">
          <h6 class="font-polonium text-xl font-bold text-gray-900">{{ section.title }}</h6>
        </div>
        <div v-if="section.rows.length > 0" class="divide-y divide-gray-200">
          <div
            v-for="(row, rowIdx) in section.rows"
            :key="`${section.title}-${rowIdx}`"
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

<script>
export default {
  name: 'ImageDetailPanel',
  props: {
    image: {
      type: Object,
      required: true
    },
    imageIndex: {
      type: Number,
      default: 0
    }
  },
  computed: {
    aiProbability() {
      return (this.image.ai_indicators && this.image.ai_indicators.ai_probability) ?? 0
    },
    softwareDetected() {
      const arr = this.image.ai_indicators && this.image.ai_indicators.software_detected
      return Array.isArray(arr) && arr.length ? arr.join(', ') : ''
    },
    anomalies() {
      const arr = this.image.ai_indicators && this.image.ai_indicators.anomalies
      return Array.isArray(arr) ? arr : []
    },
    imageSections() {
      return this.buildImageSections(this.image.metadata)
    }
  },
  methods: {
    aiChipClass(pct) {
      const n = Number(pct)
      if (n < 35) return 'status-chip-ai-low'
      if (n <= 70) return 'status-chip-ai-mid'
      return 'status-chip-ai-high'
    },
    aiChipColor(pct) {
      const n = Number(pct)
      if (n < 35) return '#00FF00'
      if (n <= 70) return '#FFFF00'
      return '#FF1493'
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
