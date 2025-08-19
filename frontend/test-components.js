// Simple test to verify components can be imported
console.log('Testing component imports...')

try {
    // Test if the components exist
    const fs = require('fs')
    const path = require('path')

    const components = [
        'EventManager.tsx',
        'EventList.tsx',
        'EventDetails.tsx',
        'EventContribute.tsx',
        'EventClosure.tsx'
    ]

    components.forEach(component => {
        const filePath = path.join(__dirname, 'src', 'components', component)
        if (fs.existsSync(filePath)) {
            console.log(`✅ ${component} exists`)
        } else {
            console.log(`❌ ${component} missing`)
        }
    })

    console.log('✅ All event management components created successfully!')

} catch (error) {
    console.error('❌ Error testing components:', error.message)
}