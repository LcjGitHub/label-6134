<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { format } from 'date-fns'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules, SelectOption } from 'naive-ui'
import { createGift, updateGift } from '../api/gift'
import { fetchCategories } from '../api/category'
import { fetchLocations } from '../api/location'
import type { Category } from '../types/category'
import type { Location } from '../types/location'
import type { Gift, GiftFormData } from '../types/gift'

const props = defineProps<{
  show: boolean
  gift: Gift | null
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  saved: []
}>()

const message = useMessage()

const formRef = ref<FormInst | null>(null)
const submitting = ref(false)
const categories = ref<Category[]>([])
const categoriesLoading = ref(false)
const locations = ref<Location[]>([])
const locationsLoading = ref(false)

const isEdit = computed(() => props.gift !== null)

const categoryOptions = computed<SelectOption[]>(() =>
  categories.value.map((c) => ({
    label: c.name,
    value: c.id,
  })),
)

const locationOptions = computed<SelectOption[]>(() =>
  locations.value.map((l) => ({
    label: l.name,
    value: l.name,
  })),
)

const defaultForm = (): GiftFormData => ({
  item_name: '',
  description: '',
  gift_date: format(new Date(), 'yyyy-MM-dd'),
  recipient_nickname: '',
  is_taken: false,
  category_id: null,
  donor_nickname: '',
  donor_phone: '',
  location: '',
})

const formModel = ref<GiftFormData>(defaultForm())

const rules: FormRules = {
  item_name: [{ required: true, message: '请输入物品名', trigger: ['blur', 'input'] }],
  gift_date: [{ required: true, message: '请选择赠送日期', trigger: ['blur', 'change'] }],
  donor_phone: [
    { required: true, message: '请输入联系电话', trigger: ['blur', 'input'] },
    {
      validator: (_rule, value) => {
        if (!/^\d{11}$/.test(value)) {
          return new Error('联系电话必须为11位数字')
        }
        return true
      },
      trigger: ['blur', 'input'],
    },
  ],
}

const modalTitle = computed(() => (isEdit.value ? '编辑赠送记录' : '新增赠送记录'))

async function loadCategories(): Promise<void> {
  categoriesLoading.value = true
  try {
    categories.value = await fetchCategories()
  } catch (e: any) {
    const msg = e?.response?.data?.error || '网络异常，类别列表加载失败'
    message.error(msg)
  } finally {
    categoriesLoading.value = false
  }
}

async function loadLocations(): Promise<void> {
  locationsLoading.value = true
  try {
    locations.value = await fetchLocations()
  } catch (e: any) {
    const msg = e?.response?.data?.error || '网络异常，地点列表加载失败'
    message.error(msg)
  } finally {
    locationsLoading.value = false
  }
}

watch(
  () => props.show,
  async (visible) => {
    if (!visible) return
    await loadCategories()
    await loadLocations()
    if (props.gift) {
      formModel.value = {
        item_name: props.gift.item_name,
        description: props.gift.description,
        gift_date: props.gift.gift_date,
        recipient_nickname: props.gift.recipient_nickname,
        is_taken: props.gift.is_taken,
        category_id: props.gift.category_id,
        donor_nickname: props.gift.donor_nickname,
        donor_phone: props.gift.donor_phone,
        location: props.gift.location,
      }
    } else {
      formModel.value = defaultForm()
    }
  },
  { immediate: true },
)

function handleClose(): void {
  emit('update:show', false)
}

async function handleSubmit(): Promise<void> {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    if (isEdit.value && props.gift) {
      await updateGift(props.gift.id, formModel.value)
    } else {
      await createGift(formModel.value)
    }
    emit('saved')
    message.success(isEdit.value ? '记录更新成功' : '记录创建成功')
  } catch (e: any) {
    const msg = e?.response?.data?.error || '提交失败，请稍后重试'
    message.error(msg)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    :title="modalTitle"
    style="width: 520px"
    :mask-closable="false"
    @update:show="emit('update:show', $event)"
  >
    <n-form
      ref="formRef"
      :model="formModel"
      :rules="rules"
      label-placement="left"
      label-width="100"
      require-mark-placement="right-hanging"
    >
      <n-form-item label="物品名" path="item_name">
        <n-input v-model:value="formModel.item_name" placeholder="例如：儿童绘本一套" />
      </n-form-item>

      <n-form-item label="物品类别" path="category_id">
        <n-select
          v-model:value="formModel.category_id"
          :options="categoryOptions"
          :loading="categoriesLoading"
          placeholder="请选择类别"
          clearable
        />
      </n-form-item>

      <n-form-item label="描述" path="description">
        <n-input
          v-model:value="formModel.description"
          type="textarea"
          placeholder="物品品相、数量等说明"
          :autosize="{ minRows: 2, maxRows: 4 }"
        />
      </n-form-item>

      <n-form-item label="赠送日期" path="gift_date">
        <n-date-picker
          v-model:formatted-value="formModel.gift_date"
          value-format="yyyy-MM-dd"
          type="date"
          style="width: 100%"
          clearable
        />
      </n-form-item>

      <n-form-item label="赠送人昵称" path="donor_nickname">
        <n-input
          v-model:value="formModel.donor_nickname"
          placeholder="赠送人社区昵称"
        />
      </n-form-item>

      <n-form-item label="联系电话" path="donor_phone">
        <n-input
          v-model:value="formModel.donor_phone"
          placeholder="11位手机号码"
          maxlength="11"
        />
      </n-form-item>

      <n-form-item label="赠送地点" path="location">
        <n-select
          v-model:value="formModel.location"
          :options="locationOptions"
          :loading="locationsLoading"
          placeholder="请选择或输入地点"
          filterable
          tag
          clearable
        />
      </n-form-item>

      <n-form-item label="接收方昵称" path="recipient_nickname">
        <n-input
          v-model:value="formModel.recipient_nickname"
          placeholder="领取人社区昵称"
        />
      </n-form-item>

      <n-form-item label="是否已取走" path="is_taken">
        <n-switch v-model:value="formModel.is_taken">
          <template #checked>已取走</template>
          <template #unchecked>待取走</template>
        </n-switch>
      </n-form-item>
    </n-form>

    <template #footer>
      <div class="footer">
        <n-button @click="handleClose">取消</n-button>
        <n-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存' : '创建' }}
        </n-button>
      </div>
    </template>
  </n-modal>
</template>

<style scoped>
.footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
