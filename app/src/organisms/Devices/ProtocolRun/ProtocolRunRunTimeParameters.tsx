import * as React from 'react'
import { useTranslation } from 'react-i18next'
import styled, { css } from 'styled-components'
import { formatRunTimeParameterDefaultValue } from '@opentrons/shared-data'
import {
  ALIGN_CENTER,
  BORDERS,
  Chip,
  COLORS,
  DIRECTION_COLUMN,
  DIRECTION_ROW,
  DISPLAY_INLINE,
  Flex,
  Icon,
  InfoScreen,
  SPACING,
  StyledText,
  TYPOGRAPHY,
  useHoverTooltip,
} from '@opentrons/components'

import { Banner } from '../../../atoms/Banner'
import { Divider } from '../../../atoms/structure'
import { Tooltip } from '../../../atoms/Tooltip'
import { useMostRecentCompletedAnalysis } from '../../LabwarePositionCheck/useMostRecentCompletedAnalysis'

import type { RunTimeParameter } from '@opentrons/shared-data'

interface ProtocolRunRuntimeParametersProps {
  runId: string
}
export function ProtocolRunRuntimeParameters({
  runId,
}: ProtocolRunRuntimeParametersProps): JSX.Element {
  const { t } = useTranslation('protocol_setup')
  const mostRecentAnalysis = useMostRecentCompletedAnalysis(runId)
  const runTimeParameters = mostRecentAnalysis?.runTimeParameters ?? []
  const hasParameter = runTimeParameters.length > 0

  const hasCustomValues = runTimeParameters.some(
    parameter => parameter.value !== parameter.default
  )

  return (
    <>
      <Flex
        flexDirection={DIRECTION_COLUMN}
        padding={SPACING.spacing16}
        gridGap={SPACING.spacing10}
      >
        <Flex
          flexDirection={DIRECTION_ROW}
          gridGap={SPACING.spacing8}
          alignItems={ALIGN_CENTER}
        >
          <StyledText as="h3" fontWeight={TYPOGRAPHY.fontWeightSemiBold}>
            {t('parameters')}
          </StyledText>
          {hasParameter ? (
            <StyledText as="label" color={COLORS.grey60}>
              {hasCustomValues ? t('custom_values') : t('default_values')}
            </StyledText>
          ) : null}
        </Flex>
        {hasParameter ? (
          <Banner
            type="informing"
            width="100%"
            iconMarginLeft={SPACING.spacing4}
          >
            <Flex flexDirection={DIRECTION_COLUMN}>
              <StyledText as="p" fontWeight={TYPOGRAPHY.fontWeightSemiBold}>
                {t('values_are_view_only')}
              </StyledText>
              <StyledText as="p">{t('cancel_and_restart_to_edit')}</StyledText>
            </Flex>
          </Banner>
        ) : null}
      </Flex>
      {!hasParameter ? (
        <Flex padding={SPACING.spacing16}>
          <InfoScreen contentType="parameters" />
        </Flex>
      ) : (
        <>
          <Divider width="100%" />
          <Flex flexDirection={DIRECTION_COLUMN} padding={SPACING.spacing16}>
            <StyledTable>
              <StyledTableHeaderContainer>
                <StyledTableHeader>{t('name')}</StyledTableHeader>
                <StyledTableHeader>{t('value')}</StyledTableHeader>
              </StyledTableHeaderContainer>
              <tbody>
                {runTimeParameters.map(
                  (parameter: RunTimeParameter, index: number) => (
                    <StyledTableRowComponent
                      key={`${index}_${parameter.variableName}`}
                      parameter={parameter}
                      index={index}
                      isLast={index === runTimeParameters.length - 1}
                      t={t}
                    />
                  )
                )}
              </tbody>
            </StyledTable>
          </Flex>
        </>
      )}
    </>
  )
}

interface StyledTableRowComponentProps {
  parameter: RunTimeParameter
  index: number
  isLast: boolean
  t: any
}

const StyledTableRowComponent = (
  props: StyledTableRowComponentProps
): JSX.Element => {
  const { parameter, index, isLast, t } = props
  const [targetProps, tooltipProps] = useHoverTooltip()
  return (
    <StyledTableRow isLast={isLast} key={`runTimeParameter-${index}`}>
      <StyledTableCell display="span">
        <StyledText
          as="p"
          css={css`
            display: inline;
            padding-right: 8px;
          `}
        >
          {parameter.displayName}
        </StyledText>
        {parameter.description != null ? (
          <>
            <Flex
              display={DISPLAY_INLINE}
              {...targetProps}
              alignItems={ALIGN_CENTER}
            >
              <Icon
                name="information"
                size={SPACING.spacing12}
                color={COLORS.grey60}
                data-testid="Icon"
              />
            </Flex>
            <Tooltip css={TYPOGRAPHY.labelRegular} tooltipProps={tooltipProps}>
              {parameter.description}
            </Tooltip>
          </>
        ) : null}
      </StyledTableCell>
      <StyledTableCell>
        <Flex flexDirection={DIRECTION_ROW} gridGap={SPACING.spacing16}>
          <StyledText as="p">
            {formatRunTimeParameterDefaultValue(parameter, t)}
          </StyledText>
          {parameter.value !== parameter.default ? (
            <Chip
              text={t('updated')}
              type="success"
              hasIcon={false}
              chipSize="small"
            />
          ) : null}
        </Flex>
      </StyledTableCell>
    </StyledTableRow>
  )
}

const StyledTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  text-align: left;
`
const StyledTableHeaderContainer = styled.thead`
  display: grid;
  grid-template-columns: 0.35fr 0.35fr;
  grid-gap: ${SPACING.spacing48};
  border-bottom: ${BORDERS.lineBorder};
`

const StyledTableHeader = styled.th`
  ${TYPOGRAPHY.labelSemiBold}
  padding-bottom: ${SPACING.spacing8};
`

interface StyledTableRowProps {
  isLast: boolean
}

const StyledTableRow = styled.tr<StyledTableRowProps>`
  display: grid;
  grid-template-columns: 0.35fr 0.35fr;
  grid-gap: ${SPACING.spacing48};
  border-bottom: ${props => (props.isLast ? 'none' : BORDERS.lineBorder)};
`

interface StyledTableCellProps {
  paddingRight?: string
  display?: string
}

const StyledTableCell = styled.td<StyledTableCellProps>`
  align-items: ${ALIGN_CENTER};
  display: ${props => (props.display != null ? props.display : 'table-cell')};
  padding: ${SPACING.spacing8} 0;
  padding-right: ${props =>
    props.paddingRight != null ? props.paddingRight : SPACING.spacing16};
`
