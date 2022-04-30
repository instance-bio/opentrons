import * as React from 'react'
import { useTranslation } from 'react-i18next'
import { useSelector } from 'react-redux'
import { useCreateLiveCommandMutation } from '@opentrons/react-api-client'
import {
  getModuleDisplayName,
  RPM,
  CELSIUS,
  HS_RPM_MAX,
  TEMP_MAX,
  HS_RPM_MIN,
  TEMP_MIN,
} from '@opentrons/shared-data'
import { Slideout } from '../../../atoms/Slideout'
import {
  COLORS,
  DIRECTION_COLUMN,
  Flex,
  FONT_WEIGHT_REGULAR,
  SPACING,
  Text,
  TYPOGRAPHY,
  useConditionalConfirm,
} from '@opentrons/components'
import { PrimaryButton } from '../../../atoms/Buttons'
import { getIsHeaterShakerAttached } from '../../../redux/config'
import { InputField } from '../../../atoms/InputField'
import { ConfirmAttachmentModal } from './ConfirmAttachmentModal'

import type { HeaterShakerModule } from '../../../redux/modules/types'
import type {
  HeaterShakerSetTargetShakeSpeedCreateCommand,
  HeaterShakerStartSetTargetTemperatureCreateCommand,
} from '@opentrons/shared-data/protocol/types/schemaV6/command/module'

interface HeaterShakerSlideoutProps {
  module: HeaterShakerModule
  onCloseClick: () => unknown
  isExpanded: boolean
  isSetShake: boolean
}

export const HeaterShakerSlideout = (
  props: HeaterShakerSlideoutProps
): JSX.Element | null => {
  const { module, onCloseClick, isExpanded, isSetShake } = props
  const { t } = useTranslation('device_details')
  const [hsValue, setHsValue] = React.useState<string | null>(null)
  const { createLiveCommand } = useCreateLiveCommandMutation()
  const moduleName = getModuleDisplayName(module.moduleModel)
  const configHasHeaterShakerAttached = useSelector(getIsHeaterShakerAttached)
  const modulePart = isSetShake ? t('shake_speed') : t('temperature')

  const sendShakeSpeedCommand = (): void => {
    if (hsValue != null && isSetShake) {
      const setShakeCommand: HeaterShakerSetTargetShakeSpeedCreateCommand = {
        commandType: 'heaterShakerModule/setTargetShakeSpeed',
        params: {
          moduleId: module.id,
          rpm: parseInt(hsValue),
        },
      }
      createLiveCommand({
        command: setShakeCommand,
      }).catch((e: Error) => {
        console.error(`error setting heater shaker shake speed: ${e.message}`)
      })
    }
    onCloseClick()
    setHsValue(null)
  }
  const {
    confirm: confirmAttachment,
    showConfirmation: showConfirmationModal,
    cancel: cancelExit,
  } = useConditionalConfirm(
    sendShakeSpeedCommand,
    !configHasHeaterShakerAttached
  )

  const sendSetTemperatureOrShakeCommand = (): void => {
    if (hsValue != null && !isSetShake) {
      const setTempCommand: HeaterShakerStartSetTargetTemperatureCreateCommand = {
        commandType: 'heaterShakerModule/startSetTargetTemperature',
        params: {
          moduleId: module.id,
          temperature: parseInt(hsValue),
        },
      }
      createLiveCommand({
        command: setTempCommand,
      }).catch((e: Error) => {
        console.error(
          `error setting module status with command type ${setTempCommand.commandType}: ${e.message}`
        )
      })
    }
    isSetShake ? confirmAttachment() : setHsValue(null)
  }

  let errorMessage
  if (isSetShake) {
    errorMessage =
      hsValue != null &&
      (parseInt(hsValue) < HS_RPM_MIN || parseInt(hsValue) > HS_RPM_MAX)
        ? t('input_out_of_range')
        : null
  } else {
    errorMessage =
      hsValue != null &&
      (parseInt(hsValue) < TEMP_MIN || parseInt(hsValue) > TEMP_MAX)
        ? t('input_out_of_range')
        : null
  }

  const inputMax = isSetShake ? HS_RPM_MAX : TEMP_MAX
  const inputMin = isSetShake ? HS_RPM_MIN : TEMP_MIN
  const unit = isSetShake ? RPM : CELSIUS

  return (
    <>
      {showConfirmationModal && (
        <ConfirmAttachmentModal
          onCloseClick={cancelExit}
          isProceedToRunModal={false}
          onConfirmClick={sendShakeSpeedCommand}
        />
      )}
      <Slideout
        title={t('set_status_heater_shaker', {
          part: modulePart,
          name: moduleName,
        })}
        onCloseClick={onCloseClick}
        isExpanded={isExpanded}
        footer={
          <PrimaryButton
            onClick={sendSetTemperatureOrShakeCommand}
            disabled={hsValue === null || errorMessage !== null}
            width="100%"
            data-testid={`HeaterShakerSlideout_btn_${module.serialNumber}`}
          >
            {t('set_temp_or_shake', { part: modulePart })}
          </PrimaryButton>
        }
      >
        <Text
          fontWeight={FONT_WEIGHT_REGULAR}
          fontSize={TYPOGRAPHY.fontSizeP}
          paddingTop={SPACING.spacing2}
          data-testid={`HeaterShakerSlideout_title_${module.serialNumber}`}
        >
          {isSetShake ? t('set_shake_of_hs') : t('set_target_temp_of_hs')}
        </Text>
        <Flex
          marginTop={SPACING.spacing4}
          flexDirection={DIRECTION_COLUMN}
          data-testid={`HeaterShakerSlideout_input_field_${module.serialNumber}`}
        >
          <Text
            fontWeight={FONT_WEIGHT_REGULAR}
            fontSize={TYPOGRAPHY.fontSizeH6}
            color={COLORS.darkGrey}
            marginBottom={SPACING.spacing1}
          >
            {isSetShake ? t('set_shake_speed') : t('set_block_temp')}
          </Text>
          <InputField
            data-testid={`${module.moduleModel}_${isSetShake}`}
            id={`${module.moduleModel}_${isSetShake}`}
            autoFocus
            units={unit}
            value={hsValue}
            onChange={e => setHsValue(e.target.value)}
            type="number"
            caption={t('module_status_range', {
              min: inputMin,
              max: inputMax,
              unit: unit,
            })}
            error={errorMessage}
          />
        </Flex>
      </Slideout>
    </>
  )
}
