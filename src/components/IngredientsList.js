import React from 'react'
import styles from './IngredientsList.css'
// import cx from 'classnames'
import get from 'lodash/get'

// TODO factor into CSS or constants or elsewhere
const swatchColors = ['blue', 'orange', 'red', 'purple', 'green', 'yellow', 'brown', 'pink']

const IngredGroupCard = ({ingredCategoryData, ingredCategoryIdx, editModeIngredientGroup, deleteIngredientGroup, ...otherProps}) => {
  if (ingredCategoryData.wells.length === 1) {
    // Single ingredient, card is rendered differently
    return (
      <div className={styles.singleIngred} >
        <IngredIndividual
          canDelete
          name={ingredCategoryData.name}
          wellName={ingredCategoryData.wells[0]}
          volume={ingredCategoryData.volume}
          concentration={ingredCategoryData.concentration}
          {...{ingredCategoryIdx, editModeIngredientGroup, deleteIngredientGroup}}
          {...otherProps} />
      </div>
    )
  }

  return (
    <section>
      <label>
        <div className={styles.circle} style={{backgroundColor: swatchColors[ingredCategoryIdx]}} />
        <div className={styles.ingredLabel}>{ingredCategoryData.name}</div>
        <div>{ingredCategoryData.wells.length} Wells</div>
      </label>

      {ingredCategoryData.individualize
          // Is individualize, allow 'wellDetails' values to override
          ? ingredCategoryData.wells.map((wellName, i) =>
            <IngredIndividual key={i}
              name={get(ingredCategoryData, ['wellDetails', wellName, 'name'], `Sample ${i + 1}`)}
              wellName={wellName}
              volume={get(ingredCategoryData, ['wellDetails', wellName, 'volume'], ingredCategoryData.volume)}
              concentration={get(ingredCategoryData, ['wellDetails', wellName, 'concentration'], ingredCategoryData.concentration)}
              {...{ingredCategoryIdx, editModeIngredientGroup, deleteIngredientGroup}}
            />
          )
          // Not individualize, but multiple wells
          : <div className={styles.ingredientInlineDetail}>
            {ingredCategoryData.wells.map((wellName, i) =>
              <div key={i}>
                <label>{wellName}</label>
                <input placeholder={ingredCategoryData.volume + ' uL'} />
              </div>
            )}
          </div>
      }

      <footer>
        <div className={styles.editButton} onClick={e => editModeIngredientGroup({group: ingredCategoryIdx})}>EDIT</div>
        <div>▼</div>
        <div className={styles.deleteIngredient} onClick={e => deleteIngredientGroup({group: ingredCategoryIdx})}>✕</div>
      </footer>
    </section>
  )
}

const IngredIndividual = ({name, wellName, volume, concentration, canDelete, ingredCategoryIdx, editModeIngredientGroup, deleteIngredientGroup, ...otherProps}) => (
  <div {...otherProps}
    className={styles.ingredientInstanceItem}
    style={{'--swatch-color': swatchColors[ingredCategoryIdx]}}
  >
    <div className={styles.leftPill}>
      <label>{name}</label>
      <button className={styles.editButton} onClick={e => editModeIngredientGroup({wellName, group: ingredCategoryIdx})}>EDIT</button>
    </div>
    <div className={styles.rightPill}>
      <input placeholder={wellName} />
      <input placeholder={volume + ' uL'} />
      <input placeholder={concentration === null ? '-' : concentration + '%'} />
      {canDelete && <div className={styles.deleteIngredient} onClick={e => deleteIngredientGroup({wellName, group: ingredCategoryIdx})}>✕</div>}
    </div>
  </div>
)

const IngredientsList = ({slotName, containerName, containerType, ingredients, editModeIngredientGroup, deleteIngredientGroup}) => (
  <div className={styles.ingredientsList}>
    <div className={styles.ingredListHeaderLabel}>
      <div>Slot {slotName}</div>
      <div>Container {containerName}</div>
    </div>
    <div>
      <div>Type {containerType}</div>
    </div>

    {ingredients.map((ingredCategoryData, i) =>
      <IngredGroupCard key={i} ingredCategoryIdx={i} {...{editModeIngredientGroup, deleteIngredientGroup, ingredCategoryData}} />)
    }

    {/* Each section is a detail view of 1 ingredient */}
    {/* Ingred category 'individualize' */}
    {/* <IngredGroupCard title='Blood Samples' swatchColor='dodgerblue'>
      <div className={styles.innerList}>
        {[1, 2, 3, 4, 5, 6, 7, 8].map(i =>
          <IngredIndividual key={i} name={`Sample ${i}`} />
        )}
      </div>
    </IngredGroupCard> */}
    {/* Single ingred */}
    {/* <div className={styles.singleIngred} >
      <IngredIndividual name='Control' swatchColor='red' canDelete />
    </div> */}
    {/* Ingred category not 'individualize' */}
    {/* <IngredGroupCard title='Buffer' swatchColor='orange'>
      <div className={styles.ingredientInlineDetail}>
        {['A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12'].map(wellName =>
          <div>
            <label>{wellName}</label>
            <input placeholder='20' />
          </div>
        )}
      </div>
    </IngredGroupCard> */}

  </div>
)

export default IngredientsList
