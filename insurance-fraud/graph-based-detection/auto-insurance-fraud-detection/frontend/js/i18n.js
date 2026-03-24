const translations = {
    en: {
        // Header & Navigation
        title: 'Auto Insurance Fraud Detection',
        logout: 'Logout',
        welcome: 'Welcome to Auto Insurance Fraud Detection',
        welcomeMsg: 'Select an option from the menu to begin analyzing fraud patterns.',
        
        // Menu sections
        claims: 'Claims',
        fraudPatterns: 'Fraud Patterns',
        fraudNetworks: 'Fraud Networks',
        analytics: 'Analytics',
        entities: 'Entities',
        
        // Claims menu
        submitClaim: 'Submit Claim',
        claimDetails: 'Claim Details',
        claimantClaims: 'Claimant Claims',
        riskScore: 'Risk Score',
        claimVelocity: 'Claim Velocity',
        fraudAnalysis: 'Fraud Analysis',
        
        // Fraud Patterns menu
        collisionRings: 'Collision Rings',
        professionalWitnesses: 'Professional Witnesses',
        collusionIndicators: 'Collusion Indicators',
        crossClaimPatterns: 'Cross-Claim Patterns',
        
        // Fraud Networks menu
        influentialClaimants: 'Influential Claimants',
        organizedRings: 'Organized Rings',
        connections: 'Connections',
        isolatedRings: 'Isolated Rings',
        
        // Analytics menu
        fraudTrends: 'Fraud Summary',
        geographicHotspots: 'Geographic Hotspots',
        claimAnomalies: 'Claim Anomalies',
        temporalPatterns: 'Temporal Patterns',
        
        // Entities menu
        repairShopStats: 'Repair Shop Stats',
        fraudHubs: 'Fraud Hubs',
        vehicleFraudHistory: 'Vehicle Fraud History',
        medicalProviderFraud: 'Medical Provider Fraud',
        
        // Common UI elements
        loading: 'Loading...',
        error: 'Error',
        noData: 'No data found',
        viewNetwork: 'View Network',
        view: 'View',
        analyze: 'Analyze',
        submit: 'Submit',
        
        // Form labels
        enterClaimantId: 'Enter Claimant ID:',
        enterClaimId: 'Enter Claim ID:',
        enterVehicleId: 'Enter Vehicle ID:',
        enterShopId: 'Enter Repair Shop ID:',
        enterProviderId: 'Enter Provider ID:',
        orSelectClaimant: 'Or Select Claimant:',
        orSelectClaim: 'Or Select Claim:',
        orSelectVehicle: 'Or Select Vehicle:',
        orSelectShop: 'Or Select Shop:',
        orSelectProvider: 'Or Select Provider:',
        selectClaimant: '-- Select Claimant --',
        selectClaim: '-- Select Claim --',
        selectVehicle: '-- Select Vehicle --',
        selectShop: '-- Select Shop --',
        selectProvider: '-- Select Provider --',
        
        // Risk levels
        lowRisk: 'Low Risk',
        mediumRisk: 'Medium Risk',
        highRisk: 'High Risk',
        corruptEntity: 'Corrupt Entity',
        corruptEntityTooltip: '* A corrupt entity is a repair shop, medical provider, witness, attorney, tow company, or passenger with a fraud score ≥ 70%.',
        ringMember: 'Part of the ring',
        
        // Error messages
        noClaimantsFound: 'No claimants found in database',
        noClaimsFound: 'No claims found',
        noVehiclesFound: 'No vehicles found',
        noShopsFound: 'No repair shops found',
        noProvidersFound: 'No providers found',
        viewNotImplemented: 'View not implemented yet',
        
        // Descriptions
        descRepairShop: 'Identifies repair shops involved in fraud schemes by analyzing their network of claims and claimants. Fraudulent shops often inflate repair costs, perform unnecessary work, or collude with claimants to stage accidents and submit false claims.',
        descMedicalProvider: 'Detects medical providers participating in billing fraud and treatment schemes. Corrupt providers may inflate treatment costs, bill for services never rendered, or collude with claimants to exaggerate injuries for higher payouts.',
        descVehicle: 'Tracks vehicles involved in multiple suspicious claims or staged accidents. Fraudsters may use the same vehicle repeatedly in different incidents, or report false damage to collect insurance payouts.',
        descClaim: 'Analyzes individual claims and their connected entities to identify fraud indicators. Examines relationships between claimants, vehicles, repair shops, and other entities involved in the claim.',
        descCollisionRings: 'Detects organized fraud rings where claimants, witnesses, and service providers repeatedly appear together across multiple claims. These collision rings stage accidents and coordinate fraudulent claims through shared networks of repair shops, medical providers, and attorneys.',
        descProfessionalWitnesses: 'Identifies witnesses who appear in an unusually high number of claims. Professional witnesses are often paid participants in staged accidents who provide false testimony to support fraudulent claims.',
        descCollusionIndicators: 'Reveals patterns of collusion between claimants and service providers. Detects suspicious relationships where the same entities repeatedly work together, indicating coordinated fraud schemes.',
        descFraudTrends: 'High-level summary of fraud activity across all claims, including approval rates, fraud scores, and suspicious entities.',
        descGeographicHotspots: 'Maps geographic areas with high concentrations of fraudulent claims. Identifies regions where fraud rings operate and helps focus investigation resources on high-risk locations.',
        descClaimAnomalies: 'Detects claims with unusually high amounts that deviate from normal patterns. Fraudsters often inflate claim values to maximize payouts, creating statistical anomalies.',
        descFraudHubs: 'Identifies central entities (repair shops, medical providers, attorneys) that serve as hubs in fraud networks. These hubs connect multiple fraudulent claims and claimants, acting as coordination points for organized fraud.',
        rationaleFraudHubs: 'A repair shop, medical provider, or attorney becomes a fraud hub when an unusually large number of claimants converge on them — especially when those claimants also share other entities (witnesses, attorneys, shops) with each other. Each box below shows one hub and the claimants connected to it. Red nodes are high-risk claimants (fraud score ≥ 70%). The collusion score measures what fraction of the hub\'s claimants share at least one other entity with another claimant in the same network — a score near 100% means nearly everyone in that hub is part of a coordinated group.',
        descInfluentialClaimants: 'Identifies claimants with high network centrality who connect to many other entities (repair shops, medical providers, attorneys). These influential nodes often indicate organized fraud rings where a central figure coordinates multiple fraudulent claims.',
        descOrganizedRings: 'Reveals collision rings where multiple claimants share the same repair shops, medical providers, witnesses, or attorneys. These organized networks coordinate staged accidents and inflated claims, with members repeatedly working together across multiple incidents.',
        descConnections: 'Maps connections between fraudsters to reveal organized fraud networks. Shows how claimants, repair shops, and service providers are linked through suspicious relationships.',
        descIsolatedRings: 'Identifies isolated fraud groups that operate independently. These rings have minimal connections to other fraud networks, making them harder to detect through traditional methods.',
        descCrossClaimPatterns: 'Detects claimants who file multiple claims with overlapping entities such as repair shops, witnesses, or attorneys. Repeated cross-claim relationships often indicate coordinated fraud activity.',
        descTemporalPatterns: 'Identifies suspicious time-based patterns in claim submissions, such as rapid filing, clustering around specific hours, or seasonal spikes that may indicate organized fraud campaigns.',
        descClaimDetails: 'View detailed information about a specific insurance claim, including the claimant, vehicle, accident details, and all connected entities such as repair shops, medical providers, and witnesses.',
        descClaimantClaims: 'Browse the complete claims history for a specific claimant. Displays all claims filed by the selected claimant along with their associated entities and fraud indicators.',
        descRiskScore: 'Calculates a fraud risk score for a claimant using a graph neural network model. The score reflects the claimant\'s network relationships and behavioral patterns across all their claims.',
        descClaimVelocity: 'Measures how frequently a claimant files insurance claims over time. Abnormally high claim velocity is a strong indicator of serial fraud or organized ring participation.',
        descFraudAnalysis: 'Provides a comprehensive fraud analysis for a claimant by combining graph algorithms and network metrics. Visualizes the claimant\'s full network of connections to identify suspicious patterns.',
        descRepairShopStats: 'Displays fraud-related statistics for a specific repair shop, including its network of claimants, claims volume, and connections to known fraud rings.',
        descVehicleFraudHistory: 'Shows the complete fraud history of a specific vehicle, including all claims filed, accidents reported, and connections to suspicious entities.',
        descMedicalProviderFraud: 'Analyzes a medical provider\'s involvement in potential fraud by examining their network of patients, claims, and billing patterns for suspicious activity.',

        // Rationale descriptions (how the algorithm works)
        rationaleCollisionRings: 'How it works: Finds claimants who filed 2+ claims, then builds their full network (claims, repair shops, accidents, witnesses, passengers, vehicles, tow companies). Claimants appearing in the same network with shared entities indicate coordinated fraud.',
        rationaleProfessionalWitnesses: 'How it works: Identifies witnesses who testified in 3 or more accidents. For each witness, shows the accidents they witnessed and the claimants involved. Repeated appearances across unrelated accidents suggest paid participation in staged incidents.',
        rationaleCollusionIndicators: 'How it works: Finds repair shops servicing 5+ claims, then maps all claimants who used those shops. When multiple claimants repeatedly use the same repair shop, it suggests a coordinated referral scheme between the shop and the claimants.',
        rationaleOrganizedRings: 'How it works: Starting from claimants with 3+ claims, discovers communities by finding claimants who share vehicles (co-ownership) or repair shops (same shop across different claims). Each ring is a connected component — members are linked through shared resources, indicating coordinated fraud activity.',
        rationaleIsolatedRings: 'How it works: Explores the 2-hop neighborhood of a selected entity, showing all directly and indirectly connected entities. Isolated groups with no connections to the broader network may represent independent fraud cells operating under the radar.',
        rationaleFraudHubs: 'How it works: Finds the top repair shops, medical providers, and attorneys ranked by the number of unique claimants connected to them. Each hub is scored for collusion: the proportion of its claimants who also share other entities (witnesses, attorneys, repair shops) with fellow claimants — a strong indicator of coordinated fraud. Colluding claimants appear larger in the graph.',
        rationaleFraudTrends: 'How it works: Aggregates fraud scores and claim counts over time to reveal temporal patterns. Spikes in fraud activity may correlate with seasonal events or indicate the emergence of new fraud rings.',
        rationaleGeographicHotspots: 'How it works: Groups claims by geographic location and calculates average fraud scores per area. Clusters of high-fraud claims in specific regions indicate localized fraud operations.',
        rationaleClaimAnomalies: 'How it works: Calculates the mean and standard deviation of claim amounts, then flags claims with z-scores exceeding 2 standard deviations. Uses Neptune ML to predict anomaly scores for each outlier claim.',
        rationaleConnections: 'How it works: Maps the direct connections between a selected claimant and all entities in their network — claims, repair shops, witnesses, vehicles, and more. Reveals the full scope of a claimant\'s involvement.',
        rationaleCrossClaimPatterns: 'How it works: Examines a claimant\'s neighborhood to find entities that appear across multiple claims. Shared repair shops, witnesses, or attorneys across different claims suggest coordinated activity.',
        rationaleTemporalPatterns: 'How it works: Analyzes the time intervals between a claimant\'s claims. Short intervals, regular patterns, or clustering around specific dates indicate systematic fraud rather than genuine incidents.',
        openSourceNote: 'This is an open-source sample. <a href="https://github.com/aws-samples/sample-fraud-detection-on-aws/tree/main/insurance-fraud/graph-based-detection/auto-insurance-fraud-detection" target="_blank" rel="noopener">Download it on GitHub</a>.'
    },
    es: {
        // Header & Navigation
        title: 'Detección de Fraude en Seguros de Auto',
        logout: 'Cerrar Sesión',
        welcome: 'Bienvenido a Detección de Fraude en Seguros de Auto',
        welcomeMsg: 'Seleccione una opción del menú para comenzar a analizar patrones de fraude.',
        
        // Menu sections
        claims: 'Reclamos',
        fraudPatterns: 'Patrones de Fraude',
        fraudNetworks: 'Redes de Fraude',
        analytics: 'Analítica',
        entities: 'Entidades',
        
        // Claims menu
        submitClaim: 'Enviar Reclamo',
        claimDetails: 'Detalles del Reclamo',
        claimantClaims: 'Reclamos del Reclamante',
        riskScore: 'Puntuación de Riesgo',
        claimVelocity: 'Velocidad de Reclamos',
        fraudAnalysis: 'Análisis de Fraude',
        
        // Fraud Patterns menu
        collisionRings: 'Anillos de Colisión',
        professionalWitnesses: 'Testigos Profesionales',
        collusionIndicators: 'Indicadores de Colusión',
        crossClaimPatterns: 'Patrones entre Reclamos',
        
        // Fraud Networks menu
        influentialClaimants: 'Reclamantes Influyentes',
        organizedRings: 'Anillos Organizados',
        connections: 'Conexiones',
        isolatedRings: 'Anillos Aislados',
        
        // Analytics menu
        fraudTrends: 'Resumen de Fraude',
        geographicHotspots: 'Puntos Calientes Geográficos',
        claimAnomalies: 'Anomalías en Reclamos',
        temporalPatterns: 'Patrones Temporales',
        
        // Entities menu
        repairShopStats: 'Estadísticas de Talleres',
        fraudHubs: 'Centros de Fraude',
        vehicleFraudHistory: 'Historial de Fraude de Vehículos',
        medicalProviderFraud: 'Fraude de Proveedores Médicos',
        
        // Common UI elements
        loading: 'Cargando...',
        error: 'Error',
        noData: 'No se encontraron datos',
        viewNetwork: 'Ver Red',
        view: 'Ver',
        analyze: 'Analizar',
        submit: 'Enviar',
        
        // Form labels
        enterClaimantId: 'Ingrese ID del Reclamante:',
        enterClaimId: 'Ingrese ID del Reclamo:',
        enterVehicleId: 'Ingrese ID del Vehículo:',
        enterShopId: 'Ingrese ID del Taller:',
        enterProviderId: 'Ingrese ID del Proveedor:',
        orSelectClaimant: 'O Seleccione Reclamante:',
        orSelectClaim: 'O Seleccione Reclamo:',
        orSelectVehicle: 'O Seleccione Vehículo:',
        orSelectShop: 'O Seleccione Taller:',
        orSelectProvider: 'O Seleccione Proveedor:',
        selectClaimant: '-- Seleccione Reclamante --',
        selectClaim: '-- Seleccione Reclamo --',
        selectVehicle: '-- Seleccione Vehículo --',
        selectShop: '-- Seleccione Taller --',
        selectProvider: '-- Seleccione Proveedor --',
        
        // Risk levels
        lowRisk: 'Riesgo Bajo',
        mediumRisk: 'Riesgo Medio',
        highRisk: 'Riesgo Alto',
        corruptEntity: 'Entidad Corrupta',
        corruptEntityTooltip: '* Una entidad corrupta es un taller, proveedor médico, testigo, abogado, empresa de grúa o pasajero con una puntuación de fraude ≥ 70%.',
        ringMember: 'Parte del anillo',
        
        // Error messages
        noClaimantsFound: 'No se encontraron reclamantes en la base de datos',
        noClaimsFound: 'No se encontraron reclamos',
        noVehiclesFound: 'No se encontraron vehículos',
        noShopsFound: 'No se encontraron talleres',
        noProvidersFound: 'No se encontraron proveedores',
        viewNotImplemented: 'Vista no implementada aún',
        
        // Descriptions
        descRepairShop: 'Identifica talleres involucrados en esquemas de fraude analizando su red de reclamos y reclamantes. Los talleres fraudulentos a menudo inflan los costos de reparación, realizan trabajos innecesarios o se confabulan con reclamantes para simular accidentes y presentar reclamos falsos.',
        descMedicalProvider: 'Detecta proveedores médicos que participan en fraude de facturación y esquemas de tratamiento. Los proveedores corruptos pueden inflar los costos de tratamiento, facturar servicios nunca prestados o confabularse con reclamantes para exagerar lesiones y obtener pagos más altos.',
        descVehicle: 'Rastrea vehículos involucrados en múltiples reclamos sospechosos o accidentes simulados. Los estafadores pueden usar el mismo vehículo repetidamente en diferentes incidentes o reportar daños falsos para cobrar pagos de seguros.',
        descClaim: 'Analiza reclamos individuales y sus entidades conectadas para identificar indicadores de fraude. Examina las relaciones entre reclamantes, vehículos, talleres y otras entidades involucradas en el reclamo.',
        descCollisionRings: 'Detecta anillos de fraude organizados donde reclamantes, testigos y proveedores de servicios aparecen repetidamente juntos en múltiples reclamos. Estos anillos de colisión simulan accidentes y coordinan reclamos fraudulentos a través de redes compartidas de talleres, proveedores médicos y abogados.',
        descProfessionalWitnesses: 'Identifica testigos que aparecen en un número inusualmente alto de reclamos. Los testigos profesionales son a menudo participantes pagados en accidentes simulados que proporcionan testimonios falsos para respaldar reclamos fraudulentos.',
        descCollusionIndicators: 'Revela patrones de colusión entre reclamantes y proveedores de servicios. Detecta relaciones sospechosas donde las mismas entidades trabajan repetidamente juntas, indicando esquemas de fraude coordinados.',
        descFraudTrends: 'Analiza patrones de fraude a lo largo del tiempo para identificar tendencias emergentes, variaciones estacionales y tácticas de fraude en evolución. Ayuda a predecir futuros puntos calientes de fraude y adaptar estrategias de detección.',
        descGeographicHotspots: 'Mapea áreas geográficas con altas concentraciones de reclamos fraudulentos. Identifica regiones donde operan anillos de fraude y ayuda a enfocar recursos de investigación en ubicaciones de alto riesgo.',
        descClaimAnomalies: 'Detecta reclamos con montos inusualmente altos que se desvían de los patrones normales. Los estafadores a menudo inflan los valores de los reclamos para maximizar los pagos, creando anomalías estadísticas.',
        descFraudHubs: 'Identifica entidades centrales (talleres, proveedores médicos, abogados) que sirven como centros en redes de fraude. Estos centros conectan múltiples reclamos y reclamantes fraudulentos, actuando como puntos de coordinación para el fraude organizado.',
        rationaleFraudHubs: 'Un taller, proveedor médico o abogado se convierte en un centro de fraude cuando un número inusualmente grande de reclamantes converge en ellos, especialmente cuando esos reclamantes también comparten otras entidades entre sí. Cada caja muestra un centro y los reclamantes conectados. Los nodos rojos son reclamantes de alto riesgo (puntuación ≥ 70%). La puntuación de colusión mide qué fracción de los reclamantes del centro comparte al menos otra entidad con otro reclamante del mismo grupo.',
        descInfluentialClaimants: 'Identifica reclamantes con alta centralidad de red que se conectan con muchas otras entidades (talleres, proveedores médicos, abogados). Estos nodos influyentes a menudo indican anillos de fraude organizados donde una figura central coordina múltiples reclamos fraudulentos.',
        descOrganizedRings: 'Revela anillos de colisión donde múltiples reclamantes comparten los mismos talleres, proveedores médicos, testigos o abogados. Estas redes organizadas coordinan accidentes simulados y reclamos inflados, con miembros trabajando repetidamente juntos en múltiples incidentes.',
        descConnections: 'Mapea conexiones entre estafadores para revelar redes de fraude organizadas. Muestra cómo los reclamantes, talleres y proveedores de servicios están vinculados a través de relaciones sospechosas.',
        descIsolatedRings: 'Identifica grupos de fraude aislados que operan independientemente. Estos anillos tienen conexiones mínimas con otras redes de fraude, lo que los hace más difíciles de detectar mediante métodos tradicionales.',
        descCrossClaimPatterns: 'Detecta reclamantes que presentan múltiples reclamos con entidades superpuestas como talleres, testigos o abogados. Las relaciones repetidas entre reclamos a menudo indican actividad de fraude coordinada.',
        descTemporalPatterns: 'Identifica patrones temporales sospechosos en la presentación de reclamos, como presentación rápida, agrupación en horarios específicos o picos estacionales que pueden indicar campañas de fraude organizadas.',
        descClaimDetails: 'Visualiza información detallada sobre un reclamo de seguro específico, incluyendo el reclamante, vehículo, detalles del accidente y todas las entidades conectadas como talleres, proveedores médicos y testigos.',
        descClaimantClaims: 'Consulta el historial completo de reclamos de un reclamante específico. Muestra todos los reclamos presentados por el reclamante seleccionado junto con sus entidades asociadas e indicadores de fraude.',
        descRiskScore: 'Calcula una puntuación de riesgo de fraude para un reclamante utilizando un modelo de red neuronal de grafos. La puntuación refleja las relaciones de red del reclamante y sus patrones de comportamiento en todos sus reclamos.',
        descClaimVelocity: 'Mide la frecuencia con la que un reclamante presenta reclamos de seguro a lo largo del tiempo. Una velocidad de reclamos anormalmente alta es un fuerte indicador de fraude serial o participación en anillos organizados.',
        descFraudAnalysis: 'Proporciona un análisis integral de fraude para un reclamante combinando algoritmos de grafos y métricas de red. Visualiza la red completa de conexiones del reclamante para identificar patrones sospechosos.',
        descRepairShopStats: 'Muestra estadísticas relacionadas con fraude para un taller específico, incluyendo su red de reclamantes, volumen de reclamos y conexiones con anillos de fraude conocidos.',
        descVehicleFraudHistory: 'Muestra el historial completo de fraude de un vehículo específico, incluyendo todos los reclamos presentados, accidentes reportados y conexiones con entidades sospechosas.',
        descMedicalProviderFraud: 'Analiza la participación de un proveedor médico en posible fraude examinando su red de pacientes, reclamos y patrones de facturación en busca de actividad sospechosa.',
        openSourceNote: 'Este es un ejemplo de código abierto. <a href="https://github.com/aws-samples/sample-fraud-detection-on-aws/tree/main/insurance-fraud/graph-based-detection/auto-insurance-fraud-detection" target="_blank" rel="noopener">Descárgalo en GitHub</a>.'
    },
    pt: {
        // Header & Navigation
        title: 'Detecção de Fraude em Seguros de Auto',
        logout: 'Sair',
        welcome: 'Bem-vindo à Detecção de Fraude em Seguros de Auto',
        welcomeMsg: 'Selecione uma opção do menu para começar a analisar padrões de fraude.',
        
        // Menu sections
        claims: 'Sinistros',
        fraudPatterns: 'Padrões de Fraude',
        fraudNetworks: 'Redes de Fraude',
        analytics: 'Análise',
        entities: 'Entidades',
        
        // Claims menu
        submitClaim: 'Enviar Sinistro',
        claimDetails: 'Detalhes do Sinistro',
        claimantClaims: 'Sinistros do Reclamante',
        riskScore: 'Pontuação de Risco',
        claimVelocity: 'Velocidade de Sinistros',
        fraudAnalysis: 'Análise de Fraude',
        
        // Fraud Patterns menu
        collisionRings: 'Anéis de Colisão',
        professionalWitnesses: 'Testemunhas Profissionais',
        collusionIndicators: 'Indicadores de Conluio',
        crossClaimPatterns: 'Padrões entre Sinistros',
        
        // Fraud Networks menu
        influentialClaimants: 'Reclamantes Influentes',
        organizedRings: 'Anéis Organizados',
        connections: 'Conexões',
        isolatedRings: 'Anéis Isolados',
        
        // Analytics menu
        fraudTrends: 'Resumo de Fraude',
        geographicHotspots: 'Pontos Quentes Geográficos',
        claimAnomalies: 'Anomalias em Sinistros',
        temporalPatterns: 'Padrões Temporais',
        
        // Entities menu
        repairShopStats: 'Estatísticas de Oficinas',
        fraudHubs: 'Centros de Fraude',
        vehicleFraudHistory: 'Histórico de Fraude de Veículos',
        medicalProviderFraud: 'Fraude de Provedores Médicos',
        
        // Common UI elements
        loading: 'Carregando...',
        error: 'Erro',
        noData: 'Nenhum dado encontrado',
        viewNetwork: 'Ver Rede',
        view: 'Ver',
        analyze: 'Analisar',
        submit: 'Enviar',
        
        // Form labels
        enterClaimantId: 'Digite o ID do Reclamante:',
        enterClaimId: 'Digite o ID do Sinistro:',
        enterVehicleId: 'Digite o ID do Veículo:',
        enterShopId: 'Digite o ID da Oficina:',
        enterProviderId: 'Digite o ID do Provedor:',
        orSelectClaimant: 'Ou Selecione Reclamante:',
        orSelectClaim: 'Ou Selecione Sinistro:',
        orSelectVehicle: 'Ou Selecione Veículo:',
        orSelectShop: 'Ou Selecione Oficina:',
        orSelectProvider: 'Ou Selecione Provedor:',
        selectClaimant: '-- Selecione Reclamante --',
        selectClaim: '-- Selecione Sinistro --',
        selectVehicle: '-- Selecione Veículo --',
        selectShop: '-- Selecione Oficina --',
        selectProvider: '-- Selecione Provedor --',
        
        // Risk levels
        lowRisk: 'Risco Baixo',
        mediumRisk: 'Risco Médio',
        highRisk: 'Risco Alto',
        corruptEntity: 'Entidade Corrupta',
        corruptEntityTooltip: '* Uma entidade corrupta é uma oficina, provedor médico, testemunha, advogado, empresa de reboque ou passageiro com pontuação de fraude ≥ 70%.',
        ringMember: 'Parte do anel',
        
        // Error messages
        noClaimantsFound: 'Nenhum reclamante encontrado no banco de dados',
        noClaimsFound: 'Nenhum sinistro encontrado',
        noVehiclesFound: 'Nenhum veículo encontrado',
        noShopsFound: 'Nenhuma oficina encontrada',
        noProvidersFound: 'Nenhum provedor encontrado',
        viewNotImplemented: 'Vista não implementada ainda',
        
        // Descriptions
        descRepairShop: 'Identifica oficinas envolvidas em esquemas de fraude analisando sua rede de sinistros e reclamantes. Oficinas fraudulentas frequentemente inflam custos de reparo, realizam trabalhos desnecessários ou conspiram com reclamantes para simular acidentes e apresentar sinistros falsos.',
        descMedicalProvider: 'Detecta provedores médicos participando de fraude de faturamento e esquemas de tratamento. Provedores corruptos podem inflar custos de tratamento, faturar serviços nunca prestados ou conspirar com reclamantes para exagerar lesões e obter pagamentos mais altos.',
        descVehicle: 'Rastreia veículos envolvidos em múltiplos sinistros suspeitos ou acidentes simulados. Fraudadores podem usar o mesmo veículo repetidamente em diferentes incidentes ou reportar danos falsos para coletar pagamentos de seguros.',
        descClaim: 'Analisa sinistros individuais e suas entidades conectadas para identificar indicadores de fraude. Examina relacionamentos entre reclamantes, veículos, oficinas e outras entidades envolvidas no sinistro.',
        descCollisionRings: 'Detecta anéis de fraude organizados onde reclamantes, testemunhas e provedores de serviços aparecem repetidamente juntos em múltiplos sinistros. Esses anéis de colisão simulam acidentes e coordenam sinistros fraudulentos através de redes compartilhadas de oficinas, provedores médicos e advogados.',
        descProfessionalWitnesses: 'Identifica testemunhas que aparecem em um número incomumente alto de sinistros. Testemunhas profissionais são frequentemente participantes pagos em acidentes simulados que fornecem testemunhos falsos para apoiar sinistros fraudulentos.',
        descCollusionIndicators: 'Revela padrões de conluio entre reclamantes e provedores de serviços. Detecta relacionamentos suspeitos onde as mesmas entidades trabalham repetidamente juntas, indicando esquemas de fraude coordenados.',
        descFraudTrends: 'Analisa padrões de fraude ao longo do tempo para identificar tendências emergentes, variações sazonais e táticas de fraude em evolução. Ajuda a prever futuros pontos quentes de fraude e adaptar estratégias de detecção.',
        descGeographicHotspots: 'Mapeia áreas geográficas com altas concentrações de sinistros fraudulentos. Identifica regiões onde anéis de fraude operam e ajuda a focar recursos de investigação em locais de alto risco.',
        descClaimAnomalies: 'Detecta sinistros com valores incomumente altos que se desviam dos padrões normais. Fraudadores frequentemente inflam valores de sinistros para maximizar pagamentos, criando anomalias estatísticas.',
        descFraudHubs: 'Identifica entidades centrais (oficinas, provedores médicos, advogados) que servem como centros em redes de fraude. Esses centros conectam múltiplos sinistros e reclamantes fraudulentos, atuando como pontos de coordenação para fraude organizada.',
        rationaleFraudHubs: 'Uma oficina, provedor médico ou advogado torna-se um centro de fraude quando um número incomumente grande de reclamantes converge neles, especialmente quando esses reclamantes também compartilham outras entidades entre si. Cada caixa mostra um centro e os reclamantes conectados. Nós vermelhos são reclamantes de alto risco (pontuação ≥ 70%). A pontuação de conluio mede qual fração dos reclamantes do centro compartilha pelo menos outra entidade com outro reclamante do mesmo grupo.',
        descInfluentialClaimants: 'Identifica reclamantes com alta centralidade de rede que se conectam com muitas outras entidades (oficinas, provedores médicos, advogados). Esses nós influentes frequentemente indicam anéis de fraude organizados onde uma figura central coordena múltiplos sinistros fraudulentos.',
        descOrganizedRings: 'Revela anéis de colisão onde múltiplos reclamantes compartilham as mesmas oficinas, provedores médicos, testemunhas ou advogados. Essas redes organizadas coordenam acidentes simulados e sinistros inflados, com membros trabalhando repetidamente juntos em múltiplos incidentes.',
        descConnections: 'Mapeia conexões entre fraudadores para revelar redes de fraude organizadas. Mostra como reclamantes, oficinas e provedores de serviços estão vinculados através de relacionamentos suspeitos.',
        descIsolatedRings: 'Identifica grupos de fraude isolados que operam independentemente. Esses anéis têm conexões mínimas com outras redes de fraude, tornando-os mais difíceis de detectar através de métodos tradicionais.',
        descCrossClaimPatterns: 'Detecta reclamantes que registram múltiplos sinistros com entidades sobrepostas como oficinas, testemunhas ou advogados. Relacionamentos repetidos entre sinistros frequentemente indicam atividade de fraude coordenada.',
        descTemporalPatterns: 'Identifica padrões temporais suspeitos na submissão de sinistros, como registro rápido, agrupamento em horários específicos ou picos sazonais que podem indicar campanhas de fraude organizadas.',
        descClaimDetails: 'Visualiza informações detalhadas sobre um sinistro de seguro específico, incluindo o reclamante, veículo, detalhes do acidente e todas as entidades conectadas como oficinas, provedores médicos e testemunhas.',
        descClaimantClaims: 'Consulta o histórico completo de sinistros de um reclamante específico. Exibe todos os sinistros registrados pelo reclamante selecionado junto com suas entidades associadas e indicadores de fraude.',
        descRiskScore: 'Calcula uma pontuação de risco de fraude para um reclamante usando um modelo de rede neural de grafos. A pontuação reflete os relacionamentos de rede do reclamante e seus padrões comportamentais em todos os seus sinistros.',
        descClaimVelocity: 'Mede a frequência com que um reclamante registra sinistros de seguro ao longo do tempo. Uma velocidade de sinistros anormalmente alta é um forte indicador de fraude serial ou participação em anéis organizados.',
        descFraudAnalysis: 'Fornece uma análise abrangente de fraude para um reclamante combinando algoritmos de grafos e métricas de rede. Visualiza a rede completa de conexões do reclamante para identificar padrões suspeitos.',
        descRepairShopStats: 'Exibe estatísticas relacionadas a fraude para uma oficina específica, incluindo sua rede de reclamantes, volume de sinistros e conexões com anéis de fraude conhecidos.',
        descVehicleFraudHistory: 'Mostra o histórico completo de fraude de um veículo específico, incluindo todos os sinistros registrados, acidentes reportados e conexões com entidades suspeitas.',
        descMedicalProviderFraud: 'Analisa o envolvimento de um provedor médico em potencial fraude examinando sua rede de pacientes, sinistros e padrões de faturamento em busca de atividade suspeita.',
        openSourceNote: 'Este é um exemplo de código aberto. <a href="https://github.com/aws-samples/sample-fraud-detection-on-aws/tree/main/insurance-fraud/graph-based-detection/auto-insurance-fraud-detection" target="_blank" rel="noopener">Baixe no GitHub</a>.'
    }
};

class I18n {
    constructor() {
        this.currentLang = localStorage.getItem('language') || 'en';
    }

    setLanguage(lang) {
        this.currentLang = lang;
        localStorage.setItem('language', lang);
        this.updateUI();
        window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
    }

    t(key) {
        return translations[this.currentLang]?.[key] || translations.en[key] || key;
    }

    updateUI() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            el.textContent = this.t(key);
        });
        document.querySelectorAll('[data-i18n-html]').forEach(el => {
            const key = el.getAttribute('data-i18n-html');
            el.innerHTML = this.t(key);
        });
        document.title = this.t('title');
    }
}

const i18n = new I18n();

// Add login page translations
translations.en.loginTitle = 'Auto Insurance Fraud Detection';
translations.en.demoLogin = 'Demo Login';
translations.en.email = 'Email';
translations.en.password = 'Password';
translations.en.enterEmail = 'Enter your email';
translations.en.enterPassword = 'Enter your password';
translations.en.login = 'Login';
translations.en.loggingIn = 'Logging in...';
translations.en.loginFailed = 'Login failed';
translations.en.enterEmailPassword = 'Please enter email and password';

translations.es.loginTitle = 'Detección de Fraude en Seguros de Auto';
translations.es.demoLogin = 'Inicio de Sesión Demo';
translations.es.email = 'Correo Electrónico';
translations.es.password = 'Contraseña';
translations.es.enterEmail = 'Ingrese su correo electrónico';
translations.es.enterPassword = 'Ingrese su contraseña';
translations.es.login = 'Iniciar Sesión';
translations.es.loggingIn = 'Iniciando sesión...';
translations.es.loginFailed = 'Error al iniciar sesión';
translations.es.enterEmailPassword = 'Por favor ingrese correo y contraseña';

translations.pt.loginTitle = 'Detecção de Fraude em Seguros de Auto';
translations.pt.demoLogin = 'Login Demo';
translations.pt.email = 'E-mail';
translations.pt.password = 'Senha';
translations.pt.enterEmail = 'Digite seu e-mail';
translations.pt.enterPassword = 'Digite sua senha';
translations.pt.login = 'Entrar';
translations.pt.loggingIn = 'Entrando...';
translations.pt.loginFailed = 'Falha no login';
translations.pt.enterEmailPassword = 'Por favor digite e-mail e senha';

// Entity type labels
translations.en.entityClaimant = 'Claimant';
translations.en.entityClaim = 'Claim';
translations.en.entityVehicle = 'Vehicle';
translations.en.entityAccident = 'Accident';
translations.en.entityRepairShop = 'Repair Shop';
translations.en.entityWitness = 'Witness';
translations.en.entityMedicalProvider = 'Medical Provider';
translations.en.entityAttorney = 'Attorney';
translations.en.entityPassenger = 'Passenger';
translations.en.entityTowCompany = 'Tow Company';

// Risk level values (from API)
translations.en.riskHigh = 'High';
translations.en.riskMedium = 'Medium';
translations.en.riskLow = 'Low';
translations.en.riskUnknown = 'Unknown';
translations.en.boolTrue = 'Yes';
translations.en.boolFalse = 'No';

translations.es.entityClaimant = 'Reclamante';
translations.es.entityClaim = 'Reclamo';
translations.es.entityVehicle = 'Vehículo';
translations.es.entityAccident = 'Accidente';
translations.es.entityRepairShop = 'Taller';
translations.es.entityWitness = 'Testigo';
translations.es.entityMedicalProvider = 'Proveedor Médico';
translations.es.entityAttorney = 'Abogado';
translations.es.entityPassenger = 'Pasajero';
translations.es.entityTowCompany = 'Empresa de Grúa';

translations.es.riskHigh = 'Alto';
translations.es.riskMedium = 'Medio';
translations.es.riskLow = 'Bajo';
translations.es.riskUnknown = 'Desconocido';
translations.es.boolTrue = 'Sí';
translations.es.boolFalse = 'No';

translations.pt.entityClaimant = 'Reclamante';
translations.pt.entityClaim = 'Sinistro';
translations.pt.entityVehicle = 'Veículo';
translations.pt.entityAccident = 'Acidente';
translations.pt.entityRepairShop = 'Oficina';
translations.pt.entityWitness = 'Testemunha';
translations.pt.entityMedicalProvider = 'Provedor Médico';
translations.pt.entityAttorney = 'Advogado';
translations.pt.entityPassenger = 'Passageiro';
translations.pt.entityTowCompany = 'Empresa de Reboque';

translations.pt.riskHigh = 'Alto';
translations.pt.riskMedium = 'Médio';
translations.pt.riskLow = 'Baixo';
translations.pt.riskUnknown = 'Desconhecido';
translations.pt.boolTrue = 'Sim';
translations.pt.boolFalse = 'Não';
