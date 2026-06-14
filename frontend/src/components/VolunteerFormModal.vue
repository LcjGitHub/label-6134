<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { format } from 'date-fns'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { createVolunteer, updateVolunteer } from '../api/volunteer'
import type { Volunteer, VolunteerFormData } from '../types/volunteer'

const props = defineProps<{
  show: boolean
  volunteer: Volunteer | null
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  saved: []
}>()

const message = useMessage()

const formRef = ref<FormInst | null>(null)
const submitting = ref(false)

const isEdit = computed(() => props.volunteer !== null)

const defaultForm = (): VolunteerFormData => ({
  name: '',
  phone: '',
  service_time: '',
  skill_category: '',
  register_date: format(new Date(), 'yyyy-MM-dd'),
  is_active: true,
})

const formModel = ref<VolunteerFormData>(defaultForm())

const rules: FormRules = {
  name: [{ required: true, message: '请输入姓名', trigger: ['blur', 'input'] }],
  phone: [
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
  register_date: [{ required: true, message: '请选择登记日期', trigger: ['blur', 'change'] }],
}

const modalTitle = computed(() => (isEdit.value ? '编辑志愿者' : '新增志愿者'))

watch(
  () => props.show,
  (visible) => {
    if (!visible) return
    if (props.volunteer) {
      formModel.value = {
        name: props.volunteer.name,
        phone: props.volunteer.phone,
        service_time: props.volunteer.service_time,
        skill_category: props.volunteer.skill_category,
        register_date: props.volunteer.register_date,
        is_active: props.volunteer.is_active,
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
    if (isEdit.value && props.volunteer) {
      await updateVolunteer(props.volunteer.id, formModel.value)
    } else {
      await createVolunteer(formModel.value)
    }
    emit('saved')
    message.success(isEdit.value ? '志愿者更新成功' : '志愿者创建成功')
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
    style="width: 500px"
    :mask-closable="false"
    @update:show="emit('update:show', $event)"
  >
    <n-form
      ref="formRef"
      :model="formModel"
      :rules="rules"
      label-placement="left"
      label-width="110"
      require-mark-placement="right-hanging"
    >
      <n-form-item label="姓名" path="name">
        <n-input v-model:value="formModel.name" placeholder="请输入志愿者姓名" />
      </n-form-item>

      <n-form-item label="联系电话" path="phone">
        <n-input
          v-model:value="formModel.phone"
          placeholder="11位手机号码"
          maxlength="11"
        />
      </n-form-item>

      <n-form-item label="可服务时段" path="service_time">
        <n-input
          v-model:value="formModel.service_time"
          placeholder="例如：工作日晚上、周末全天"
        />
      </n-form-item>

      <n-form-item label="擅长协助类别" path="skill_category">
        <n-input
          v-model:value="formModel.skill_category"
          placeholder="例如：家电维修、儿童辅导、法律咨询"
        />
      </n-form-item>

      <n-form-item label="登记日期" path="register_date">
        <n-date-picker
          v-model:formatted-value="formModel.register_date"
          value-format="yyyy-MM-dd"
          type="date"
          style="width: 100%"
          clearable
        />
      </n-form-item>

      <n-form-item label="是否在职" path="is_active">
        <n-switch v-model:value="formModel.is_active">
          <template #checked>在职</template>
          <template #unchecked>离职</template>
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
