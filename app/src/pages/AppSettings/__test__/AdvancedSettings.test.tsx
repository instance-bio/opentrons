import * as React from 'react'
import { MemoryRouter } from 'react-router-dom'
import { resetAllWhenMocks } from 'jest-when'
import { screen } from '@testing-library/react'

import { renderWithProviders } from '@opentrons/components'

import { i18n } from '../../../i18n'
import * as Config from '../../../redux/config'
import {
  AdditionalCustomLabwareSourceFolder,
  ClearUnavailableRobots,
  EnableDevTools,
  OT2AdvancedSettings,
  OverridePathToPython,
  PreventRobotCaching,
  ShowHeaterShakerAttachmentModal,
  ShowLabwareOffsetSnippets,
  U2EInformation,
} from '../../../organisms/AdvancedSettings'

import { AdvancedSettings } from '../AdvancedSettings'

jest.mock('../../../redux/config')
jest.mock('../../../redux/calibration')
jest.mock('../../../redux/custom-labware')
jest.mock('../../../redux/discovery')
jest.mock('../../../redux/protocol-analysis')
jest.mock('../../../redux/system-info')
jest.mock('@opentrons/components/src/hooks')
jest.mock('../../../redux/analytics')
jest.mock('../../../organisms/AdvancedSettings')

const render = (): ReturnType<typeof renderWithProviders> => {
  return renderWithProviders(
    <MemoryRouter>
      <AdvancedSettings />
    </MemoryRouter>,
    {
      i18nInstance: i18n,
    }
  )
}

const mockGetChannelOptions = Config.getUpdateChannelOptions as jest.MockedFunction<
  typeof Config.getUpdateChannelOptions
>
const mockPreventRobotCaching = PreventRobotCaching as jest.MockedFunction<
  typeof PreventRobotCaching
>

const mockOT2AdvancedSettings = OT2AdvancedSettings as jest.MockedFunction<
  typeof OT2AdvancedSettings
>
const mockEnableDevTools = EnableDevTools as jest.MockedFunction<
  typeof EnableDevTools
>
const mockU2EInformation = U2EInformation as jest.MockedFunction<
  typeof U2EInformation
>
const mockShowLabwareOffsetSnippets = ShowLabwareOffsetSnippets as jest.MockedFunction<
  typeof ShowLabwareOffsetSnippets
>
const mockClearUnavailableRobots = ClearUnavailableRobots as jest.MockedFunction<
  typeof ClearUnavailableRobots
>
const mockOverridePathToPython = OverridePathToPython as jest.MockedFunction<
  typeof OverridePathToPython
>
const mockShowHeaterShakerAttachmentModal = ShowHeaterShakerAttachmentModal as jest.MockedFunction<
  typeof ShowHeaterShakerAttachmentModal
>
const mockAdditionalCustomLabwareSourceFolder = AdditionalCustomLabwareSourceFolder as jest.MockedFunction<
  typeof AdditionalCustomLabwareSourceFolder
>

describe('AdvancedSettings', () => {
  beforeEach(() => {
    mockGetChannelOptions.mockReturnValue([
      {
        label: 'Stable',
        value: 'latest',
      },
      { label: 'Beta', value: 'beta' },
      { label: 'Alpha', value: 'alpha' },
    ])
    mockPreventRobotCaching.mockReturnValue(<div>mock PreventRobotCaching</div>)
    mockOT2AdvancedSettings.mockReturnValue(<div>mock OT2AdvancedSettings</div>)
    mockEnableDevTools.mockReturnValue(<div>mock EnableDevTools</div>)
    mockU2EInformation.mockReturnValue(<div>mock U2EInformation</div>)
    mockShowLabwareOffsetSnippets.mockReturnValue(
      <div>mock ShowLabwareOffsetSnippets</div>
    )
    mockClearUnavailableRobots.mockReturnValue(
      <div>mock ClearUnavailableRobots</div>
    )
    mockOverridePathToPython.mockReturnValue(
      <div>mock OverridePathToPython</div>
    )
    mockShowHeaterShakerAttachmentModal.mockReturnValue(
      <div>mock ShowHeaterShakerAttachmentModal</div>
    )
    mockAdditionalCustomLabwareSourceFolder.mockReturnValue(
      <div>mock AdditionalCustomLabwareSourceFolder</div>
    )
  })

  afterEach(() => {
    jest.resetAllMocks()
    resetAllWhenMocks()
  })

  it('renders correct titles', () => {
    const [{ getByText }] = render()
    getByText('Update Channel')
  })

  it('renders the update channel combobox and section', () => {
    const [{ getByText, getByRole }] = render()
    getByText(
      'Stable receives the latest stable releases. Beta allows you to try out new in-progress features before they launch in Stable channel, but they have not completed testing yet.'
    )
    getByRole('combobox', { name: '' })
  })

  it('should render mock OT-2 Advanced Settings Tip Length Calibration Method section', () => {
    render()
    screen.getByText('mock AdditionalCustomLabwareSourceFolder')
  })

  it('should render mock OT-2 Advanced Settings Tip Length Calibration Method section', () => {
    render()
    screen.getByText('mock OT2AdvancedSettings')
  })

  it('should render mock robot caching section', () => {
    render()
    screen.getByText('mock PreventRobotCaching')
  })

  it('should render mock U2EInformation', () => {
    render()
    expect(screen.getByText('mock U2EInformation'))
  })

  it('should render mock show link to get labware offset data section', () => {
    render()
    screen.getByText('mock ShowLabwareOffsetSnippets')
  })

  it('should render mock ShowHeaterShakerAttachmentModal section', () => {
    render()
    screen.getByText('mock ShowHeaterShakerAttachmentModal')
  })

  it('should render mock OverridePathToPython section', () => {
    render()
    screen.getByText('mock OverridePathToPython')
  })

  it('should render mock clear unavailable robots section', () => {
    render()
    screen.getByText('mock ClearUnavailableRobots')
  })

  it('should render mock developer tools section', () => {
    render()
    screen.getByText('mock EnableDevTools')
  })
})
