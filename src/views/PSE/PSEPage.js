import React, { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Search, Building2, ExternalLink, ChevronRight, X,
  Globe2, FlaskConical, Satellite, Newspaper, AlertCircle, User
} from 'lucide-react';
import * as d3 from 'd3';
import pseCompanies from '../../data/pse_companies.json';
import PSENavBar from './PSENavBar';
import Footer from '../../components/Footer';

// ─── Mock engagement data (to be replaced with real CRM data) ─────────────────

const MOCK_ENGAGEMENT = {
  'Aon Plc':          { status: 'Partner',  models: ['ECCO', 'ISSM', 'GRACE'],          date: '2023-03' },
  'BlackRock':        { status: 'Partner',  models: ['ISSM', 'CMS-Flux', 'GRACE'],       date: '2022-11' },
  'Arbol':            { status: 'Partner',  models: ['RAPID', 'GRACE', 'SWOT'],          date: '2022-06' },
  'AccuWeather':      { status: 'Active',   models: ['RAPID', 'LES', 'EDMF'],            date: '2023-08' },
  'NCX':              { status: 'Active',   models: ['CMS-Flux', 'CARDAMOM'],            date: '2023-01' },
  'AIR Parametric':   { status: 'Active',   models: ['RAPID', 'ECCO'],                   date: '2023-05' },
  'Bloomberg':        { status: 'Active',   models: ['CMS-Flux', 'ECCO'],               date: '2023-09' },
  'BASF':             { status: 'Active',   models: ['CARDAMOM', 'RAPID', 'GRACE'],      date: '2023-04' },
  'Carbon Direct':    { status: 'Active',   models: ['CMS-Flux', 'CARDAMOM'],            date: '2023-07' },
  'Dynamical.org':    { status: 'Active',   models: ['RAPID', 'GRACE', 'SWOT'],          date: '2023-02' },
  'Climavision':      { status: 'Prospect', models: ['LES', 'EDMF', 'RAPID'],            date: '2024-03' },
  'Amundi':           { status: 'Prospect', models: ['ISSM', 'CMS-Flux'],               date: '2024-01' },
  'Arch Insurance':   { status: 'Prospect', models: ['RAPID', 'ISSM'],                   date: '2024-02' },
  'Hazen and Sawyer': { status: 'Prospect', models: ['RAPID', 'GRACE'],                  date: '2024-01' },
  'Stripe / Frontier':{ status: 'Prospect', models: ['CMS-Flux', 'CARDAMOM'],            date: '2023-11' },
  'Agrograph':        { status: 'Alumni',   models: ['RAPID', 'CARDAMOM'],               date: '2021-06' },
  'Agrograph Inc.':   { status: 'Alumni',   models: ['RAPID', 'CARDAMOM'],               date: '2021-06' },
  'Ponterra':         { status: 'Alumni',   models: ['CMS-Flux', 'CARDAMOM'],            date: '2022-03' },
};

const STATUS_META = {
  Partner:  { label: 'Partner',  color: 'bg-green-100 text-green-800 border-green-200' },
  Active:   { label: 'Active',   color: 'bg-blue-100 text-blue-800 border-blue-200' },
  Prospect: { label: 'Prospect', color: 'bg-amber-100 text-amber-800 border-amber-200' },
  Alumni:   { label: 'Alumni',   color: 'bg-gray-100 text-gray-600 border-gray-200' },
};

// ─── Mock news articles (to be replaced with live feed) ───────────────────────

// ─── Guardian News API (live) ─────────────────────────────────────────────────

// News is pre-fetched nightly by scripts/fetch_guardian_news.js (cron 10:00 UTC = 2am PT).
// The React app reads the static file: instant load, no API key in client.
const NEWS_JSON_URL = `${process.env.PUBLIC_URL}/guardian_news.json`;

const autoTagModels = (text) => {
  const t = text.toLowerCase();
  const tags = [];
  if (/grace|groundwater|aquifer|gravity recovery/.test(t)) tags.push('GRACE');
  if (/swot|surface water|river level|lake level|ocean topograph/.test(t)) tags.push('SWOT');
  if (/streamflow|flood|river discharge|hydrology|watershed/.test(t)) tags.push('RAPID');
  if (/co2 flux|carbon flux|cms.flux|greenhouse gas emission/.test(t)) tags.push('CMS-Flux');
  if (/soil carbon|terrestrial carbon|ecosystem carbon|cardamom/.test(t)) tags.push('CARDAMOM');
  if (/ice sheet|sea.level rise|glacier|greenland|antarctica|issm/.test(t)) tags.push('ISSM');
  if (/\bocean\b|marine|sea surface temperature|ecco/.test(t)) tags.push('ECCO');
  if (/tropospheric|air quality|ozone|methane retrieval|tropess/.test(t)) tags.push('TROPESS');
  return tags;
};

const autoTagSectors = (text) => {
  const t = text.toLowerCase();
  const tags = [];
  if (/insur|parametric|catastrophe|reinsur|underwr/.test(t)) tags.push('Insurance');
  if (/invest|portfolio|asset manag|esg|blackrock|bloomberg|amundi/.test(t)) tags.push('Finance');
  if (/\bfarm\b|crop|agricultur|irrigation|harvest|agri/.test(t)) tags.push('Agriculture');
  if (/wind energy|solar|renewable|power grid|offshore wind/.test(t)) tags.push('Energy');
  if (/water utility|water supply|groundwater manag/.test(t)) tags.push('Water Management');
  if (/carbon credit|carbon market|offset|nature.based/.test(t)) tags.push('Carbon & Conservation');
  if (/sea.level|coastal flood|storm surge/.test(t)) tags.push('Coastal Ocean');
  return tags;
};

const ALUMNI_JSON_URL = `${process.env.PUBLIC_URL}/jpl_alumni.json`;

// Company name → regex for detecting mentions in news article text
const COMPANY_PATTERNS = [
  { name: 'Planet Labs',      re: /planet labs/i },
  { name: 'Maxar',            re: /\bmaxar\b/i },
  { name: 'Capella Space',    re: /capella space/i },
  { name: 'Spire',            re: /\bspire\b(?! of)/i },
  { name: 'Muon Space',       re: /muon space/i },
  { name: 'BlackSky',         re: /blacksky/i },
  { name: 'ICEYE',            re: /\biceye\b/i },
  { name: 'Carbon Mapper',    re: /carbon mapper/i },
  { name: 'GHGSat',           re: /ghgsat/i },
  { name: 'Kayrros',          re: /kayrros/i },
  { name: 'Descartes Labs',   re: /descartes labs/i },
  { name: 'Satelligence',     re: /satelligence/i },
  { name: 'Overstory',        re: /\boverstory\b/i },
  { name: 'Jupiter Intel',    re: /jupiter intelligence/i },
  { name: 'Tomorrow.io',      re: /tomorrow\.io/i },
  { name: 'One Concern',      re: /one concern/i },
  { name: 'WattTime',         re: /watttime/i },
  { name: 'Zesty.ai',         re: /zesty\.ai/i },
  { name: 'Climavision',      re: /climavision/i },
  { name: 'KatRisk',          re: /katrisk/i },
  { name: 'Boeing',           re: /\bboeing\b/i },
  { name: 'Lockheed Martin',  re: /lockheed martin/i },
  { name: 'Leidos',           re: /\bleidos\b/i },
  { name: 'RTX',              re: /\braytheon\b|\brtx\b/i },
  { name: 'BAE Systems',      re: /bae systems/i },
  { name: 'MITRE',            re: /\bmitre\b/i },
  { name: 'Microsoft',        re: /\bmicrosoft\b/i },
  { name: 'Google',           re: /\bgoogle\b/i },
  { name: 'Amazon',           re: /\bamazon\b/i },
  { name: 'Apple',            re: /\bapple\b(?! cider| pie| orchard)/i },
  { name: 'NVIDIA',           re: /\bnvidia\b/i },
  { name: 'Meta',             re: /\bmeta\b(?! ?data| ?analysis)/i },
  { name: 'IBM',              re: /\bibm\b/i },
  { name: 'Esri',             re: /\besri\b/i },
  { name: 'BlackRock',        re: /blackrock/i },
  { name: 'Goldman Sachs',    re: /goldman sachs/i },
  { name: 'JP Morgan',        re: /jp\s?morgan|jpmorgan/i },
  { name: 'Amundi',           re: /\bamundi\b/i },
  { name: 'Verisk',           re: /\bverisk\b/i },
  { name: 'Munich Re',        re: /munich re/i },
  { name: 'Swiss Re',         re: /swiss re/i },
  { name: 'Chubb',            re: /\bchubb\b/i },
  { name: 'Aon',              re: /\baon\b/i },
  { name: "Moody's",          re: /moody'?s/i },
  { name: 'S&P Global',       re: /s&p global|s&p 500/i },
  { name: 'AccuWeather',      re: /accuweather/i },
  { name: 'Bloomberg',        re: /\bbloomberg\b/i },
  { name: 'Arbol',            re: /\barbol\b/i },
  { name: 'NCX',              re: /\bncx\b/i },
  { name: 'Carbon Direct',    re: /carbon direct/i },
  { name: 'BASF',             re: /\bbasf\b/i },
  { name: 'Deloitte',         re: /\bdeloitte\b/i },
  { name: 'KPMG',             re: /\bkpmg\b/i },
  { name: 'PwC',              re: /\bpwc\b|pricewaterhousecoopers/i },
  { name: 'BCG',              re: /boston consulting group|\bbcg\b/i },
  { name: 'EDF',              re: /environmental defense fund/i },
  { name: 'WRI',              re: /world resources institute|\bwri\b/i },
  { name: 'RMI',              re: /rocky mountain institute|\brmi\b/i },
];

const MODEL_COLORS = {
  RAPID: '#3B82F6', CARDAMOM: '#10B981', 'CMS-Flux': '#F59E0B',
  ECCO: '#8B5CF6', ISSM: '#06B6D4', 'MOMO-CHEM': '#EF4444',
  LES: '#2E8B57', EDMF: '#FF6347', GRACE: '#D946EF',
  SWOT: '#0EA5E9', TROPESS: '#0EA5E9',
};

// ─── Model / Mission definitions ─────────────────────────────────────────────

const ALL_MODELS = [
  {
    name: 'RAPID', type: 'model', color: '#3B82F6', domain: 'Hydrology',
    industryPitch: 'Forecast river discharge and flood risk across millions of stream reaches, from irrigation planning to parametric insurance triggers.',
    path: '/RAPID',
    website: 'http://rapid-hub.org/',
  },
  {
    name: 'CARDAMOM', type: 'model', color: '#10B981', domain: 'Carbon Cycle',
    industryPitch: 'Quantify terrestrial carbon stocks, soil moisture, and ecosystem dynamics for carbon markets, nature-based investment, and agricultural risk.',
    path: '/CARDAMOM',
    website: 'https://cardamom-framework.github.io/CARDAMOM',
  },
  {
    name: 'CMS-Flux', type: 'model', color: '#F59E0B', domain: 'Carbon Flux',
    industryPitch: 'Satellite-verified CO₂ flux data for emissions accounting, carbon credit verification, ESG reporting, and regulatory compliance.',
    path: '/CMS-Flux',
    website: 'https://cmsflux.jpl.nasa.gov/',
  },
  {
    name: 'ECCO', type: 'model', color: '#8B5CF6', domain: 'Oceanography',
    industryPitch: 'Full-depth ocean state data for maritime routing, offshore energy planning, coastal hazard assessment, and hurricane risk quantification.',
    path: '/ECCO',
    website: 'https://ecco-group.org/',
  },
  {
    name: 'ISSM', type: 'model', color: '#06B6D4', domain: 'Glaciology',
    industryPitch: 'Probabilistic sea-level rise projections from ice sheet dynamics for long-horizon coastal asset valuation and infrastructure planning.',
    path: '/ISSM',
    website: 'https://issm.jpl.nasa.gov/',
  },
  {
    name: 'MOMO-CHEM', type: 'model', color: '#EF4444', domain: 'Atmospheric Chemistry',
    industryPitch: 'Tropospheric pollutant reanalysis for air quality products, environmental liability underwriting, and health risk assessment.',
    path: '/MOMO-CHEM',
    website: null,
  },
  {
    name: 'LES', type: 'model', color: '#2E8B57', domain: 'Atmospheric Modeling',
    industryPitch: 'High-fidelity boundary layer turbulence simulations for wind energy micrositing, structural load analysis, and atmospheric design standards.',
    path: '/LES',
    website: null,
  },
  {
    name: 'EDMF', type: 'model', color: '#FF6347', domain: 'Atmospheric Modeling',
    industryPitch: 'Turbulent mixing parameterizations that improve wind, solar, and precipitation forecasts for energy, agriculture, and grid operators.',
    path: '/EDMF',
    website: null,
  },
  {
    name: 'GRACE', type: 'mission', color: '#D946EF', domain: 'Geophysics & Geodesy',
    industryPitch: 'Monthly groundwater and ice mass change data for water stress monitoring, drought insurance design, and sea-level rise projections.',
    path: '/GRACE',
    website: 'https://gracefo.jpl.nasa.gov/',
  },
  {
    name: 'SWOT', type: 'mission', color: '#0EA5E9', domain: 'Ocean & Hydrology',
    industryPitch: 'First global sub-kilometer survey of surface water elevations for flood mapping, reservoir management, and coastal hazard early warning.',
    path: '/SWOT',
    website: 'https://swot.jpl.nasa.gov/',
  },
  {
    name: 'TROPESS', type: 'mission', color: '#F97316', domain: 'Atmospheric Chemistry',
    industryPitch: 'NASA CrIS/AIRS-based atmospheric profiling of ozone, CO, and other trace gases, enabling air quality forecasting, regulatory compliance, and pollution source attribution.',
    path: '/TROPESS',
    website: 'https://tropess.gesdisc.eosdis.nasa.gov/',
  },
];

// ─── Sector → model mapping with use cases ───────────────────────────────────

const SECTOR_MAP = {
  'Agriculture': {
    emoji: '🌾',
    tagline: 'Precision farming, irrigation management, and agricultural carbon markets',
    models: [
      { name: 'RAPID', useCase: 'Simulates river discharge across thousands of reaches, enabling irrigation scheduling and flood damage forecasting for farms along river floodplains.' },
      { name: 'CARDAMOM', useCase: 'Bayesian retrieval of soil moisture dynamics and terrestrial carbon stocks supports crop stress monitoring and precision agriculture decision tools.' },
      { name: 'CMS-Flux', useCase: 'Tracks regional carbon fluxes to power agricultural carbon credit programs and verifiable Scope 3 emissions accounting in food supply chains.' },
      { name: 'GRACE', useCase: 'Measures monthly groundwater storage anomalies to detect aquifer depletion rates, essential for sustainable irrigation planning in water-stressed regions.' },
      { name: 'SWOT', useCase: 'Global river and lake water level surveys enable precision irrigation planning and early drought warning for crop production.' },
    ],
  },
  'Insurance': {
    emoji: '🛡️',
    tagline: 'Climate risk quantification for flood, drought, air quality, and sea-level products',
    models: [
      { name: 'RAPID', useCase: 'High-resolution river discharge modeling quantifies flood inundation probability across thousands of reaches for parametric insurance product design.' },
      { name: 'GRACE', useCase: 'Groundwater depletion and drought severity trends support parametric drought insurance triggers and agricultural risk underwriting.' },
      { name: 'SWOT', useCase: 'Flood extent and inundation depth at unprecedented spatial resolution calibrate actuarial flood models and parametric policy triggers.' },
      { name: 'ISSM', useCase: 'Probabilistic sea-level rise projections from Greenland and Antarctic ice sheets over 20–50 year horizons for coastal property underwriting.' },
      { name: 'ECCO', useCase: 'Ocean heat content and circulation modeling quantifies hurricane intensification risk relevant to wind and flood coverage.' },
      { name: 'MOMO-CHEM', useCase: 'Tropospheric pollutant concentration trends support environmental liability underwriting and health-related claims analysis.' },
    ],
  },
  'Finance': {
    emoji: '📈',
    tagline: 'Carbon markets, ESG risk, climate-adjusted asset pricing, and commodity risk',
    models: [
      { name: 'CMS-Flux', useCase: 'Satellite-verified atmospheric CO₂ flux data for carbon credit pricing integrity and voluntary carbon market additionality verification.' },
      { name: 'CARDAMOM', useCase: 'Terrestrial carbon sequestration uncertainty quantification for nature-based investment due diligence and science-based credit validation.' },
      { name: 'GRACE', useCase: 'Regional groundwater anomalies affect commodity futures pricing and agricultural asset valuations in water-scarce basins.' },
      { name: 'ECCO', useCase: 'Ocean state data informs maritime shipping cost models, port congestion risk pricing, and climate-adjusted coastal asset valuation.' },
      { name: 'ISSM', useCase: 'Probabilistic sea-level scenarios for climate-adjusted pricing of coastal real estate, municipal bonds, and long-duration infrastructure debt.' },
    ],
  },
  'Energy': {
    emoji: '⚡',
    tagline: 'Renewable energy siting, emissions tracking, and offshore operations',
    models: [
      { name: 'LES', useCase: 'High-fidelity boundary layer turbulence simulations for wind farm micrositing, wake modeling, and annual energy production optimization.' },
      { name: 'EDMF', useCase: 'Turbulent mixing parameterizations improve solar irradiance and wind speed forecasting, reducing energy dispatch uncertainty for grid operators.' },
      { name: 'MOMO-CHEM', useCase: 'Atmospheric chemistry reanalysis establishes pollution baselines around energy facilities and supports air quality regulatory permitting.' },
      { name: 'CMS-Flux', useCase: 'CO₂ emission flux tracking enables Scope 1/2 emissions accounting and independent carbon neutrality verification for energy companies.' },
      { name: 'ECCO', useCase: 'Subsurface ocean temperature and current data inform offshore wind turbine structural design and ocean thermal energy conversion site selection.' },
    ],
  },
  'Water Management': {
    emoji: '💧',
    tagline: 'Basin-wide water allocation, groundwater monitoring, and flood operations',
    models: [
      { name: 'RAPID', useCase: 'Routes continental-scale streamflow across river networks for basin-wide water rights adjudication and drought response planning.' },
      { name: 'GRACE', useCase: 'The only global monitoring of groundwater storage changes, enabling long-range water utility supply planning and depletion alerts.' },
      { name: 'SWOT', useCase: 'Reservoir and river level monitoring at global scale informs water allocation decisions, flood control operations, and treaty compliance.' },
      { name: 'ECCO', useCase: 'Ocean freshwater flux and coastal salinity data support desalination site selection and coastal water quality management.' },
    ],
  },
  'Analytics': {
    emoji: '📊',
    tagline: 'Earth science data products and APIs for AI/ML, geospatial platforms, and decision support',
    models: [
      { name: 'RAPID', useCase: 'Gridded streamflow time series and global routing network data for hydrological ML model training and flood risk platform development.' },
      { name: 'CARDAMOM', useCase: 'Ensemble carbon cycle parameter and state variable outputs for ecosystem analytics and nature-based solutions data products.' },
      { name: 'CMS-Flux', useCase: 'Global gridded CO₂ flux fields for atmospheric inversion analytics and carbon accounting platform integration.' },
      { name: 'ECCO', useCase: 'Full-depth ocean state variables (temperature, salinity, velocity) as structured geospatial data streams for maritime analytics platforms.' },
      { name: 'ISSM', useCase: 'Ice sheet dynamics outputs for sea-level rise analytics and climate scenario modeling in risk platform development.' },
      { name: 'MOMO-CHEM', useCase: 'Multi-species tropospheric chemistry reanalysis fields for air quality analytics, exposure mapping, and health risk modeling.' },
      { name: 'LES', useCase: 'High-resolution 3D turbulence fields for boundary layer process analytics and atmospheric model validation datasets.' },
      { name: 'EDMF', useCase: 'Atmospheric mixing parameterization data for NWP model improvement analytics and convection scheme benchmarking.' },
      { name: 'GRACE', useCase: 'Gridded total water storage anomalies for water cycle analytics, drought indexing, and climate trend analysis platforms.' },
      { name: 'SWOT', useCase: 'Global surface water elevation rasters and time series for hydrological analytics, change detection, and flood mapping products.' },
    ],
  },
  'Weather & Climate': {
    emoji: '🌦️',
    tagline: 'Forecast improvement, climate risk products, and atmospheric analysis services',
    models: [
      { name: 'LES', useCase: 'Resolves turbulent boundary layer physics at meter scale to improve numerical weather prediction accuracy and atmospheric parameterization.' },
      { name: 'EDMF', useCase: 'Convective mass-flux parameterization advances reduce systematic precipitation forecast errors in operational weather models.' },
      { name: 'MOMO-CHEM', useCase: 'Chemical reanalysis products power air quality forecast services and support climate attribution analysis for litigation and regulatory use.' },
      { name: 'ECCO', useCase: 'Ocean heat content and mixed-layer initialization improves seasonal climate prediction skill for agriculture and energy businesses.' },
      { name: 'RAPID', useCase: 'Hydrological routing for flash flood guidance products and real-time streamflow forecasting in national weather service operations.' },
      { name: 'GRACE', useCase: 'Terrestrial water storage anomalies provide drought monitoring signals for seasonal hydrological outlooks and commodity risk products.' },
      { name: 'SWOT', useCase: 'Near-real-time lake and river level data for hydrological data assimilation, improving flood forecast accuracy in operational systems.' },
    ],
  },
  'Supply Chain': {
    emoji: '🚚',
    tagline: 'Climate disruption risk, maritime routing, and supply chain carbon accounting',
    models: [
      { name: 'RAPID', useCase: 'Identifies flood-driven bottlenecks in logistics networks near river corridors to quantify supply chain disruption risk and business continuity exposure.' },
      { name: 'ECCO', useCase: 'Ocean current and mesoscale eddy data for fuel-optimal maritime routing optimization and port operational planning.' },
      { name: 'GRACE', useCase: 'Regional water stress indicators for climate-smart agricultural sourcing risk assessment and supplier resilience scoring.' },
      { name: 'CMS-Flux', useCase: 'Carbon accounting across geographically distributed supply chains using gridded emission flux attribution data.' },
    ],
  },
  'Utilities': {
    emoji: '🔌',
    tagline: 'Water supply, hydropower, grid management, and infrastructure resilience',
    models: [
      { name: 'LES', useCase: 'Wind boundary layer characterization for distributed energy resource (DER) siting and power grid load variability forecasting.' },
      { name: 'EDMF', useCase: 'Atmospheric boundary layer mixing improves load forecast models for electric grid operators managing renewable integration.' },
      { name: 'RAPID', useCase: 'Streamflow forecasting for hydropower dispatch scheduling and municipal water intake management during drought or flood events.' },
      { name: 'GRACE', useCase: 'Groundwater storage monitoring to support long-range water utility supply planning, aquifer management, and rate-setting decisions.' },
      { name: 'SWOT', useCase: 'Reservoir and river level monitoring for hydropower generation planning and municipal water supply reliability assessments.' },
      { name: 'ECCO', useCase: 'Coastal ocean temperature data for desalination efficiency optimization and once-through cooling system operations compliance.' },
    ],
  },
  'Consumer Goods': {
    emoji: '🛍️',
    tagline: 'Scope 3 emissions, water footprint, and deforestation-free sourcing',
    models: [
      { name: 'CMS-Flux', useCase: 'Satellite-based carbon flux attribution supports Scope 3 supply chain emissions reporting and deforestation-free sourcing verification.' },
      { name: 'CARDAMOM', useCase: 'Land-use carbon change quantification for deforestation-free sourcing commitments and forest risk commodity due diligence.' },
      { name: 'RAPID', useCase: 'Watershed-level water consumption data supports water footprint calculations for water-intensive manufacturing operations.' },
    ],
  },
  'Environmental Health': {
    emoji: '🫁',
    tagline: 'Air quality monitoring, pollution source attribution, and public health risk assessment',
    models: [
      { name: 'MOMO-CHEM', useCase: 'Multi-constituent tropospheric reanalysis tracks pollutant exposure concentrations across population centers for health risk assessment products.' },
      { name: 'CMS-Flux', useCase: 'Identifies regional emission source attribution for regulatory compliance analysis and environmental justice impact assessment.' },
      { name: 'CARDAMOM', useCase: 'Ecosystem moisture dynamics and fire danger indices inform wildfire smoke exposure models affecting community health.' },
    ],
  },
  'Coastal Ocean': {
    emoji: '🌊',
    tagline: 'Coastal hazard assessment, ocean monitoring, and marine industry planning',
    models: [
      { name: 'ECCO', useCase: 'Full-depth ocean state estimation for coastal inundation modeling, storm surge forecasting, and marine ecosystem health monitoring.' },
      { name: 'SWOT', useCase: 'Coastal sea surface height measurements at sub-kilometer resolution enable real-time storm surge and tidal flood early warning systems.' },
      { name: 'GRACE', useCase: 'Decomposes sea-level change into ice-mass and terrestrial water components for coastal resilience planning and adaptation investment.' },
    ],
  },
  'Carbon & Conservation': {
    emoji: '🌿',
    tagline: 'Carbon offset verification, ecosystem monitoring, and nature-based solutions',
    models: [
      { name: 'CMS-Flux', useCase: 'Independent atmospheric inversion-based verification of forest carbon offset claims for voluntary carbon market integrity.' },
      { name: 'CARDAMOM', useCase: 'Scientifically rigorous ecosystem carbon baseline estimates for additionality assessment in conservation and reforestation projects.' },
    ],
  },
  'Energy & Infrastructure': {
    emoji: '🏗️',
    tagline: 'Infrastructure resilience, renewable siting, and offshore asset management',
    models: [
      { name: 'LES', useCase: 'Turbulent wind load modeling for structural design standards of wind turbines, bridges, and tall infrastructure assets.' },
      { name: 'EDMF', useCase: 'Atmospheric turbulence characterization supports wind loading design standards and infrastructure siting decisions.' },
      { name: 'ECCO', useCase: 'Subsurface ocean current and temperature data for offshore pipeline integrity management and submarine cable installation planning.' },
      { name: 'RAPID', useCase: 'Flood risk modeling and return period estimates for transportation infrastructure siting and FEMA compliance requirements.' },
      { name: 'GRACE', useCase: 'Land subsidence detection from groundwater extraction for pipeline safety monitoring and infrastructure integrity management.' },
    ],
  },
  'Sustainability': {
    emoji: '♻️',
    tagline: 'ESG verification, science-based targets, and net-zero pathway assessment',
    models: [
      { name: 'CMS-Flux', useCase: 'Third-party satellite-based carbon flux verification for corporate sustainability reporting and CDP climate disclosure.' },
      { name: 'CARDAMOM', useCase: 'Land carbon cycle modeling for science-based target (SBTi) setting and net-zero pathway credibility assessment.' },
      { name: 'RAPID', useCase: 'Water scarcity metrics and watershed depletion indicators for CDP water disclosure and water stewardship target setting.' },
      { name: 'GRACE', useCase: 'Groundwater trend data for corporate water stewardship targets and nature-positive commitments in water-stressed regions.' },
    ],
  },
  'Non-profit': {
    emoji: '🤝',
    tagline: 'Environmental mission support, open science data, and policy analysis',
    models: [
      { name: 'CMS-Flux', useCase: 'Open-access carbon flux data supports environmental advocacy, policy analysis, and climate litigation evidence development.' },
      { name: 'CARDAMOM', useCase: 'Ecosystem carbon and biodiversity dynamics data for conservation advocacy and nature-based solutions project evaluation.' },
      { name: 'GRACE', useCase: 'Groundwater and drought data for water equity advocacy and community resilience program design.' },
      { name: 'RAPID', useCase: 'River flow data for environmental flow advocacy, freshwater biodiversity assessment, and watershed restoration planning.' },
    ],
  },
  'Communications': {
    emoji: '📡',
    tagline: 'Atmospheric effects on satellite and wireless signal propagation',
    models: [
      { name: 'LES', useCase: 'High-resolution atmospheric turbulence data for satellite signal propagation modeling and microwave link budget planning.' },
      { name: 'EDMF', useCase: 'Tropospheric mixing layer height dynamics affect signal strength for microwave and millimeter-wave communication systems.' },
    ],
  },
  'Consulting': {
    emoji: '💼',
    tagline: 'Scientific methodology, data licensing, and climate risk advisory services',
    models: [
      { name: 'RAPID', useCase: 'Validated hydrological modeling methodology and global river network data for client flood risk advisory practices.' },
      { name: 'CMS-Flux', useCase: 'Carbon flux data and methodology for climate advisory and corporate emissions verification consulting practices.' },
      { name: 'ECCO', useCase: 'Ocean state data and methodology for maritime, coastal, and climate risk consulting engagements.' },
      { name: 'ISSM', useCase: 'Sea-level rise modeling methodology for coastal adaptation consulting and infrastructure investment advisory.' },
    ],
  },
  'Space/Wildfire': {
    emoji: '🔥',
    tagline: 'Wildfire emission tracking, smoke dispersion, and fire behavior modeling',
    models: [
      { name: 'MOMO-CHEM', useCase: 'Smoke chemistry and dispersion modeling for wildfire air quality impact assessment and community health alert systems.' },
      { name: 'CMS-Flux', useCase: 'Fire carbon emission quantification and cumulative forest carbon loss accounting for wildfire economic damage estimation.' },
      { name: 'LES', useCase: 'Pyroconvection and fire-atmosphere interaction dynamics modeling for extreme wildfire behavior prediction.' },
    ],
  },
  'Climate': {
    emoji: '🌍',
    tagline: 'Physical climate risk analytics, scenario modeling, and attribution science',
    models: [
      { name: 'ECCO', useCase: 'Ocean heat content and sea level data for climate scenario analysis and physical risk assessment frameworks.' },
      { name: 'ISSM', useCase: 'Ice sheet dynamics for long-horizon sea-level rise projections under various emissions scenarios.' },
      { name: 'CMS-Flux', useCase: 'Atmospheric CO₂ flux data for climate attribution science and policy analysis.' },
      { name: 'GRACE', useCase: 'Total water storage and ice mass trends for climate change detection and attribution research.' },
      { name: 'RAPID', useCase: 'Hydrological cycle changes for precipitation and runoff trend analysis under climate scenarios.' },
    ],
  },
  'Other': {
    emoji: '🔬',
    tagline: 'Custom engagement opportunities across Earth science applications',
    models: [
      { name: 'RAPID', useCase: 'Custom applications in river hydrology and water resources assessment for specialized industries.' },
      { name: 'ECCO', useCase: 'Custom applications in ocean science and maritime operations research.' },
      { name: 'CMS-Flux', useCase: 'Custom applications in carbon monitoring and greenhouse gas accounting services.' },
    ],
  },
};

// ─── Sector badge colors ──────────────────────────────────────────────────────

const SECTOR_COLORS = {
  'Agriculture': 'bg-green-100 text-green-800 border-green-200',
  'Insurance': 'bg-blue-100 text-blue-800 border-blue-200',
  'Finance': 'bg-yellow-100 text-yellow-800 border-yellow-200',
  'Energy': 'bg-orange-100 text-orange-800 border-orange-200',
  'Water Management': 'bg-cyan-100 text-cyan-800 border-cyan-200',
  'Analytics': 'bg-purple-100 text-purple-800 border-purple-200',
  'Carbon & Conservation': 'bg-emerald-100 text-emerald-800 border-emerald-200',
  'Consumer Goods': 'bg-pink-100 text-pink-800 border-pink-200',
  'Weather & Climate': 'bg-sky-100 text-sky-800 border-sky-200',
  'Environmental Health': 'bg-lime-100 text-lime-800 border-lime-200',
  'Coastal Ocean': 'bg-teal-100 text-teal-800 border-teal-200',
  'Supply Chain': 'bg-amber-100 text-amber-800 border-amber-200',
  'Utilities': 'bg-indigo-100 text-indigo-800 border-indigo-200',
  'Sustainability': 'bg-green-100 text-green-800 border-green-200',
  'Non-profit': 'bg-rose-100 text-rose-800 border-rose-200',
  'Communications': 'bg-violet-100 text-violet-800 border-violet-200',
  'Consulting': 'bg-slate-100 text-slate-800 border-slate-200',
  'Space/Wildfire': 'bg-red-100 text-red-800 border-red-200',
  'Energy & Infrastructure': 'bg-orange-100 text-orange-800 border-orange-200',
  'Climate': 'bg-blue-100 text-blue-800 border-blue-200',
  'Other': 'bg-gray-100 text-gray-800 border-gray-200',
};

// ─── Shared micro-components ──────────────────────────────────────────────────

const SectorBadge = ({ sector }) => {
  const colors = SECTOR_COLORS[sector] || 'bg-gray-100 text-gray-800 border-gray-200';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${colors}`}>
      {sector}
    </span>
  );
};

const ModelBadge = ({ name, color }) => (
  <span
    className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium text-white"
    style={{ backgroundColor: color }}
  >
    {name}
  </span>
);

// ─── Hero ─────────────────────────────────────────────────────────────────────

const Hero = ({ companiesCount, sectorsCount }) => (
  <div className="bg-gradient-to-br from-indigo-900 via-blue-900 to-slate-900 text-white rounded-lg shadow-sm mb-6 py-10 px-8">
    <h2 className="text-3xl font-bold mb-2">Connecting Earth Science to Industry</h2>
    <p className="text-blue-100 max-w-2xl mb-8">
      NASA's Earth models and satellite missions generate actionable data products for agriculture,
      finance, energy, water management, and more. Explore how your sector connects to NASA science.
    </p>
    <div className="flex flex-wrap gap-4">
      {[
        { value: companiesCount, label: 'Engaged Companies' },
        { value: sectorsCount, label: 'Industry Sectors' },
        { value: 3, label: 'Earth Missions' },
        { value: 3, label: 'Earth Models' },
      ].map(({ value, label }) => (
        <div key={label} className="bg-white/10 backdrop-blur rounded-xl px-6 py-3 text-center min-w-[110px]">
          <div className="text-2xl font-bold">{value}</div>
          <div className="text-xs text-indigo-200 mt-0.5">{label}</div>
        </div>
      ))}
    </div>
  </div>
);

// ─── Alumni Network Graph ─────────────────────────────────────────────────────

const FEATURED_NODES = [
  { id: 'GRACE',   type: 'mission', color: '#D946EF', label: 'GRACE' },
  { id: 'SWOT',    type: 'mission', color: '#0EA5E9', label: 'SWOT' },
  { id: 'TROPESS', type: 'mission', color: '#F97316', label: 'TROPESS' },
  { id: 'ECCO',    type: 'model',   color: '#8B5CF6', label: 'ECCO' },
  { id: 'ISSM',    type: 'model',   color: '#06B6D4', label: 'ISSM' },
  { id: 'CMS-Flux',type: 'model',   color: '#F59E0B', label: 'CMS-Flux' },
];

const AlumniNetworkGraph = ({ alumni }) => {
  const svgRef = useRef(null);
  const [tooltip, setTooltip] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const { nodes, links } = useMemo(() => {
    const companiesWithAlumni = Object.entries(alumni)
      .filter(([, p]) => p.length > 0)
      .sort((a, b) => b[1].length - a[1].length);

    const companyToSectorModel = {};
    companiesWithAlumni.forEach(([company]) => {
      const entry = pseCompanies.find(c => c.company === company);
      if (!entry) return;
      const sectorModels = (SECTOR_MAP[entry.sector] || { models: [] }).models
        .map(m => m.name)
        .filter(m => FEATURED_NODES.some(n => n.id === m));
      companyToSectorModel[company] = sectorModels;
    });

    const nodes = [
      ...FEATURED_NODES.map(n => ({ ...n, nodeType: n.type, radius: 26 })),
      ...companiesWithAlumni.map(([company, people]) => ({
        id: company,
        nodeType: 'company',
        color: '#64748b',
        label: company,
        alumniCount: people.length,
        radius: 8 + Math.min(people.length * 3, 14),
      })),
    ];

    const links = [];
    companiesWithAlumni.forEach(([company]) => {
      (companyToSectorModel[company] || []).forEach(modelId => {
        links.push({ source: modelId, target: company, type: 'sector' });
      });
    });

    return { nodes, links };
  }, [alumni]);

  const draw = useCallback(() => {
    const el = svgRef.current;
    if (!el || nodes.length === 0) return;

    const W = el.clientWidth || 780;
    const H = 480;

    const svg = d3.select(el);
    svg.selectAll('*').remove();
    svg.attr('viewBox', `0 0 ${W} ${H}`);

    const g = svg.append('g');

    // Zoom
    svg.call(
      d3.zoom().scaleExtent([0.4, 3]).on('zoom', e => g.attr('transform', e.transform))
    );

    // Simulation
    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(d => {
        const src = nodes.find(n => n.id === (d.source.id || d.source));
        return src && (src.nodeType === 'mission' || src.nodeType === 'model') ? 110 : 60;
      }).strength(0.6))
      .force('charge', d3.forceManyBody().strength(d =>
        d.nodeType === 'mission' || d.nodeType === 'model' ? -300 : -80
      ))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide(d => d.radius + 6));

    // Links
    const link = g.append('g').selectAll('line')
      .data(links).join('line')
      .attr('stroke', '#cbd5e1').attr('stroke-width', 1).attr('stroke-opacity', 0.5);

    // Node groups
    const node = g.append('g').selectAll('g')
      .data(nodes).join('g')
      .attr('cursor', 'pointer')
      .call(
        d3.drag()
          .on('start', (event, d) => { if (!event.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
          .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
          .on('end', (event, d) => { if (!event.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
      )
      .on('mousemove', (event, d) => {
        const rect = el.getBoundingClientRect();
        setTooltipPos({ x: event.clientX - rect.left + 12, y: event.clientY - rect.top - 10 });
        setTooltip(d);
      })
      .on('mouseleave', () => setTooltip(null));

    // Glow filter
    const defs = svg.append('defs');
    const filter = defs.append('filter').attr('id', 'pse-glow');
    filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur');
    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    // Circles
    node.append('circle')
      .attr('r', d => d.radius)
      .attr('fill', d => d.color)
      .attr('fill-opacity', d => d.nodeType === 'company' ? 0.75 : 0.9)
      .attr('stroke', d => d.color)
      .attr('stroke-width', d => (d.nodeType === 'mission' || d.nodeType === 'model') ? 2 : 1)
      .attr('filter', d => (d.nodeType === 'mission' || d.nodeType === 'model') ? 'url(#pse-glow)' : null);

    // Labels (only mission/model + larger companies)
    node.filter(d => d.nodeType === 'mission' || d.nodeType === 'model' || d.alumniCount >= 2)
      .append('text')
      .text(d => d.label)
      .attr('text-anchor', 'middle')
      .attr('dy', d => d.radius + 11)
      .attr('font-size', d => (d.nodeType === 'mission' || d.nodeType === 'model') ? 11 : 9)
      .attr('font-weight', d => (d.nodeType === 'mission' || d.nodeType === 'model') ? '700' : '500')
      .attr('fill', d => (d.nodeType === 'mission' || d.nodeType === 'model') ? d.color : '#475569');

    // Icon letter inside mission/model nodes
    node.filter(d => d.nodeType === 'mission' || d.nodeType === 'model')
      .append('text')
      .text(d => d.id[0])
      .attr('text-anchor', 'middle').attr('dy', '0.35em')
      .attr('font-size', 12).attr('font-weight', '800').attr('fill', 'white');

    sim.on('tick', () => {
      link
        .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
  }, [nodes, links]);

  useEffect(() => { draw(); }, [draw]);

  const companyCount = nodes.filter(n => n.nodeType === 'company').length;

  return (
    <div className="relative">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">NASA Alumni Network</h3>
          <p className="text-xs text-gray-400 mt-0.5">
            {companyCount} companies · 6 NASA missions &amp; models · connections via shared research focus
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-400">
          {[
            { color: '#D946EF', label: 'Mission' },
            { color: '#8B5CF6', label: 'Model' },
            { color: '#64748b', label: 'Company' },
          ].map(({ color, label }) => (
            <span key={label} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: color }} />
              {label}
            </span>
          ))}
        </div>
      </div>

      <div className="relative bg-slate-50 rounded-xl border border-gray-200 overflow-hidden">
        <svg ref={svgRef} className="w-full" style={{ height: 480 }} />
        {tooltip && (
          <div
            className="pointer-events-none absolute z-10 bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-xs max-w-[200px]"
            style={{ left: tooltipPos.x, top: tooltipPos.y }}
          >
            <p className="font-semibold text-gray-800">{tooltip.label}</p>
            {tooltip.nodeType === 'mission' && <p className="text-indigo-500 mt-0.5">NASA Mission</p>}
            {tooltip.nodeType === 'model' && <p className="text-purple-500 mt-0.5">NASA Model</p>}
            {tooltip.nodeType === 'company' && (
              <p className="text-gray-500 mt-0.5">{tooltip.alumniCount} NASA alumni</p>
            )}
          </div>
        )}
      </div>
      <p className="text-xs text-gray-400 mt-1.5 text-right">Drag nodes · scroll to zoom</p>
    </div>
  );
};

// ─── Sector Explorer ──────────────────────────────────────────────────────────

const SectorExplorer = ({ sectorCounts, alumni }) => {
  const [selectedSector, setSelectedSector] = useState(null);
  const [companySearch, setCompanySearch] = useState('');
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [openTopCompany, setOpenTopCompany] = useState(null);


  const sortedSectors = useMemo(() =>
    Object.keys(SECTOR_MAP)
      .filter(s => (sectorCounts[s] || 0) > 0)
      .sort((a, b) => (sectorCounts[b] || 0) - (sectorCounts[a] || 0)),
    [sectorCounts]
  );

  const sectorCompanies = useMemo(() => {
    if (!selectedSector) return [];
    return pseCompanies
      .filter(c => {
        const match = c.sector === selectedSector;
        const searchMatch = !companySearch || c.company.toLowerCase().includes(companySearch.toLowerCase());
        return match && searchMatch;
      })
      .sort((a, b) => {
        const aC = (alumni[a.company] || []).length;
        const bC = (alumni[b.company] || []).length;
        if (bC !== aC) return bC - aC;
        return a.company.localeCompare(b.company);
      });
  }, [selectedSector, companySearch, alumni]);

  const sectorAlumniCounts = useMemo(() => {
    const counts = {};
    pseCompanies.forEach(({ company, sector }) => {
      const n = (alumni[company] || []).length;
      if (n > 0) counts[sector] = (counts[sector] || 0) + n;
    });
    return counts;
  }, [alumni]);

  const topCompanies = useMemo(() =>
    Object.entries(alumni)
      .filter(([, p]) => p.length > 0)
      .sort((a, b) => b[1].length - a[1].length),
    [alumni]
  );

  const totalAlumni = useMemo(() =>
    Object.values(alumni).reduce((s, a) => s + a.length, 0),
    [alumni]
  );

  const companiesWithAlumni = useMemo(() =>
    Object.values(alumni).filter(a => a.length > 0).length,
    [alumni]
  );

  const sectorData = selectedSector ? SECTOR_MAP[selectedSector] : null;

  const handleSelect = (sector) => {
    setSelectedSector(sector);
    setCompanySearch('');
    setSelectedCompany(null);
  };

  return (
    <div className="flex gap-6">
      {/* Left sidebar: sector list */}
      <div className="w-60 flex-shrink-0">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1 px-1">
          {sortedSectors.length} Sectors
        </p>
        <p className="text-xs text-gray-400 mb-3 px-1">Number = companies per sector</p>
        <div className="space-y-0.5">
          {sortedSectors.map(sector => {
            const alumniCount = sectorAlumniCounts[sector] || 0;
            const isSelected = selectedSector === sector;
            return (
              <button
                key={sector}
                onClick={() => handleSelect(sector)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left ${
                  isSelected ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <span className="flex items-center gap-1.5 min-w-0">
                  {alumniCount > 0 && (
                    <span className="w-1.5 h-1.5 rounded-full bg-violet-400 flex-shrink-0" />
                  )}
                  <span className="truncate">{sector}</span>
                </span>
                <div className="flex items-center gap-1 flex-shrink-0 ml-1">
                  <span
                    title="Number of companies in this sector"
                    className={`text-xs px-1.5 py-0.5 rounded-full ${
                      isSelected ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'
                    }`}
                  >
                    {sectorCounts[sector] || 0}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Right: detail panel */}
      <div className="flex-1 min-w-0">
        {!selectedSector ? (
          <div className="space-y-6">
            {/* Alumni Network Graph */}
            {Object.keys(alumni).length > 0 && (
              <AlumniNetworkGraph alumni={alumni} />
            )}


            {/* Top companies */}
            {topCompanies.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                  Top Companies by NASA Alumni (click to view)
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {topCompanies.slice(0, 12).map(([company, people]) => {
                    const isOpen = openTopCompany === company;
                    return (
                      <div key={company} className={`rounded-xl border transition-all ${isOpen ? 'border-violet-300 shadow-md col-span-2' : 'border-gray-200 shadow-sm hover:shadow-md hover:border-violet-200'}`}>
                        <button
                          onClick={() => setOpenTopCompany(isOpen ? null : company)}
                          className="w-full flex items-center justify-between px-4 py-3 text-left"
                        >
                          <div>
                            <p className={`text-sm font-semibold ${isOpen ? 'text-violet-700' : 'text-gray-800'}`}>{company}</p>
                            <p className="text-xs text-gray-400 mt-0.5">{people.length} NASA alumni</p>
                          </div>
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${isOpen ? 'bg-violet-100 text-violet-700' : 'bg-gray-100 text-gray-600'}`}>
                            {people.length}
                          </div>
                        </button>
                        {isOpen && (
                          <div className="border-t border-violet-100 divide-y divide-gray-100">
                            {people.map((person, i) => (
                              <div key={i} className="flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50">
                                <div className="w-8 h-8 rounded-full bg-violet-100 flex items-center justify-center flex-shrink-0 text-violet-700 text-xs font-bold">
                                  {person.name.split(' ').filter(Boolean).map(n => n[0]).join('')}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-semibold text-gray-900">{person.name}</p>
                                  <p className="text-xs text-gray-500 truncate">{person.title}</p>
                                </div>
                                <a href={person.linkedin} target="_blank" rel="noopener noreferrer"
                                  className="flex-shrink-0 flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium">
                                  LinkedIn <ExternalLink size={11} />
                                </a>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Sectors with alumni, clickable */}
            {Object.keys(sectorAlumniCounts).length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                  Sectors with NASA Connections (click to explore)
                </h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(sectorAlumniCounts)
                    .sort((a, b) => b[1] - a[1])
                    .map(([sector, count]) => (
                      <button
                        key={sector}
                        onClick={() => handleSelect(sector)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-50 border border-violet-200 text-violet-700 rounded-full text-sm font-medium hover:bg-violet-100 transition-colors"
                      >
                        {sector}
                        <span className="bg-violet-200 text-violet-800 rounded-full px-1.5 text-xs font-bold">
                          {count}
                        </span>
                      </button>
                    ))}
                </div>
              </div>
            )}

            {totalAlumni === 0 && (
              <div className="flex flex-col items-center justify-center h-40 text-center text-gray-400">
                <Globe2 size={48} className="mb-3 opacity-25" />
                <p className="text-sm mt-1">Select a sector to explore NASA models and missions</p>
              </div>
            )}
          </div>
        ) : (
          <div>
            {/* Sector header */}
            <div className="mb-6 flex items-start gap-4">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{selectedSector}</h2>
                <p className="text-gray-500 mt-0.5">{sectorData.tagline}</p>
                <p className="text-sm text-indigo-600 font-medium mt-2">
                  {sectorCounts[selectedSector] || 0} companies in this sector · connected via shared NASA research focus
                </p>
              </div>
            </div>

            {/* Model/mission cards */}
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Relevant NASA Models &amp; Missions ({sectorData.models.length})
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
              {sectorData.models.map(({ name, useCase }) => {
                const model = ALL_MODELS.find(m => m.name === name);
                if (!model) return null;
                return (
                  <div
                    key={name}
                    className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: model.color }} />
                        <span className="font-semibold text-gray-900">{name}</span>
                        <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 font-medium">
                          {model.type === 'mission' ? 'Mission' : 'Model'}
                        </span>
                      </div>
                      <Link
                        to={model.path}
                        className="text-xs text-blue-500 hover:text-blue-700 flex items-center gap-0.5 font-medium transition-colors"
                      >
                        Dashboard <ChevronRight size={12} />
                      </Link>
                    </div>
                    <p className="text-xs text-gray-400 mb-2">{model.domain}</p>
                    <p className="text-sm text-gray-700 leading-relaxed">{useCase}</p>
                  </div>
                );
              })}
            </div>

            {/* Company list */}
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Companies in This Sector
              </h3>
              <div className="relative">
                <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Filter companies..."
                  value={companySearch}
                  onChange={e => setCompanySearch(e.target.value)}
                  className="pl-7 pr-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 w-52"
                />
                {companySearch && (
                  <button
                    onClick={() => setCompanySearch('')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <X size={13} />
                  </button>
                )}
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              {sectorCompanies.length === 0 ? (
                <p className="text-center text-gray-400 py-8 text-sm">No companies match your search</p>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-px bg-gray-100">
                  {sectorCompanies.map(({ company }, i) => {
                    const companyAlumni = alumni[company] || [];
                    const isSelected = selectedCompany === company;
                    return (
                      <button
                        key={`${company}-${i}`}
                        onClick={() => setSelectedCompany(isSelected ? null : company)}
                        className={`flex items-center justify-between px-4 py-2.5 gap-2 w-full text-left transition-colors ${
                          isSelected ? 'bg-blue-50' : 'bg-white hover:bg-gray-50'
                        }`}
                      >
                        <span className="flex items-center gap-2 min-w-0">
                          <Building2 size={13} className="text-gray-300 flex-shrink-0" />
                          <span className="text-sm text-gray-700 truncate" title={company}>{company}</span>
                        </span>
                        {companyAlumni.length > 0 && (
                          <span className="flex-shrink-0 flex items-center gap-0.5 text-xs px-1.5 py-0.5 bg-violet-100 text-violet-700 rounded-full font-medium">
                            <User size={10} />
                            {companyAlumni.length}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Alumni panel */}
            {selectedCompany && (() => {
              const selectedAlumni = alumni[selectedCompany] || [];
              return (
                <div className="mt-3 border border-gray-200 rounded-xl overflow-hidden">
                  <div className="flex items-center px-4 py-3 bg-gray-50 border-b border-gray-200 gap-2">
                    <User size={14} className="text-violet-500" />
                    <span className="text-sm font-semibold text-gray-800">NASA Alumni at {selectedCompany}</span>
                    {selectedAlumni.length > 0 && (
                      <span className="text-xs px-1.5 py-0.5 bg-violet-100 text-violet-700 rounded-full">{selectedAlumni.length}</span>
                    )}
                  </div>
                  {selectedAlumni.length === 0 ? (
                    <p className="text-center text-gray-400 py-6 text-sm">No NASA alumni found for this company</p>
                  ) : (
                    <div className="divide-y divide-gray-100">
                      {selectedAlumni.map((person, i) => (
                        <div key={i} className="flex items-center gap-4 px-4 py-3 hover:bg-gray-50">
                          <div className="w-9 h-9 rounded-full bg-violet-100 flex items-center justify-center flex-shrink-0 text-violet-700 text-xs font-bold">
                            {person.name.split(' ').filter(Boolean).map(n => n[0]).join('')}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-gray-900">{person.name}</p>
                            <p className="text-xs text-gray-600 truncate">{person.title}</p>
                            {person.snippet && (
                              <p className="text-xs text-gray-400 mt-0.5 truncate">
                                {person.snippet.replace(/&#39;/g, "'").replace(/&amp;/g, '&')}
                              </p>
                            )}
                          </div>
                          <a
                            href={person.linkedin}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-shrink-0 flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
                          >
                            LinkedIn <ExternalLink size={11} />
                          </a>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })()}

            {sectorCompanies.length > 0 && (
              <p className="text-xs text-gray-400 mt-2 text-right">
                {sectorCompanies.length} {sectorCompanies.length === 1 ? 'company' : 'companies'}
                {sectorCompanies.filter(c => (alumni[c.company] || []).length > 0).length > 0 && (
                  <span className="ml-2 text-violet-500">
                    · {sectorCompanies.filter(c => (alumni[c.company] || []).length > 0).length} with NASA alumni
                  </span>
                )}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// ─── Company Directory ────────────────────────────────────────────────────────

const CompanyDirectory = ({ sectorCounts, alumni }) => {
  const [search, setSearch] = useState('');
  const [sectorFilter, setSectorFilter] = useState('all');
  const [modelFilter, setModelFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [alumniOnly, setAlumniOnly] = useState(false);
  const [page, setPage] = useState(0);
  const PER_PAGE = 50;

  const modelColorMap = useMemo(() => {
    const map = {};
    ALL_MODELS.forEach(m => { map[m.name] = m.color; });
    return map;
  }, []);

  const sectorModelMap = useMemo(() => {
    const map = {};
    Object.entries(SECTOR_MAP).forEach(([sector, data]) => {
      map[sector] = data.models.map(m => m.name);
    });
    return map;
  }, []);

  const filtered = useMemo(() => {
    return pseCompanies.filter(c => {
      const searchMatch = !search || c.company.toLowerCase().includes(search.toLowerCase());
      const sectorMatch = sectorFilter === 'all' || c.sector === sectorFilter;
      const models = sectorModelMap[c.sector] || [];
      const modelMatch = modelFilter === 'all' || models.includes(modelFilter);
      const eng = MOCK_ENGAGEMENT[c.company];
      const statusMatch = statusFilter === 'all' || (eng && eng.status === statusFilter);
      const alumniMatch = !alumniOnly || (alumni[c.company] || []).length > 0;
      return searchMatch && sectorMatch && modelMatch && statusMatch && alumniMatch;
    });
  }, [search, sectorFilter, modelFilter, statusFilter, alumniOnly, sectorModelMap, alumni]);

  const paginated = useMemo(() =>
    filtered.slice(page * PER_PAGE, (page + 1) * PER_PAGE),
    [filtered, page]
  );

  const totalPages = Math.ceil(filtered.length / PER_PAGE);
  const allSectors = Object.keys(SECTOR_MAP).sort();
  const hasFilters = search || sectorFilter !== 'all' || modelFilter !== 'all' || statusFilter !== 'all' || alumniOnly;

  const resetFilters = () => {
    setSearch('');
    setSectorFilter('all');
    setModelFilter('all');
    setStatusFilter('all');
    setAlumniOnly(false);
    setPage(0);
  };

  const handleSearch = v => { setSearch(v); setPage(0); };
  const handleSector = v => { setSectorFilter(v); setPage(0); };
  const handleModel = v => { setModelFilter(v); setPage(0); };
  const handleStatus = v => { setStatusFilter(v); setPage(0); };

  return (
    <div>
      {/* Filter row */}
      <div className="flex flex-wrap gap-3 mb-5">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search companies..."
            value={search}
            onChange={e => handleSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 bg-white"
          />
          {search && (
            <button onClick={() => handleSearch('')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
              <X size={14} />
            </button>
          )}
        </div>

        <select
          value={sectorFilter}
          onChange={e => handleSector(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 bg-white"
        >
          <option value="all">All Sectors</option>
          {allSectors.map(s => (
            <option key={s} value={s}>{s} ({sectorCounts[s] || 0})</option>
          ))}
        </select>

        <select
          value={modelFilter}
          onChange={e => handleModel(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 bg-white"
        >
          <option value="all">All Models &amp; Missions</option>
          {ALL_MODELS.map(m => (
            <option key={m.name} value={m.name}>{m.name} ({m.type})</option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={e => handleStatus(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 bg-white"
        >
          <option value="all">All Statuses</option>
          {Object.keys(STATUS_META).map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <button
          onClick={() => { setAlumniOnly(v => !v); setPage(0); }}
          className={`flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border transition-colors ${
            alumniOnly
              ? 'bg-violet-600 text-white border-violet-600'
              : 'text-gray-600 border-gray-200 hover:bg-gray-50'
          }`}
        >
          <User size={13} /> NASA Alumni
        </button>

        {hasFilters && (
          <button
            onClick={resetFilters}
            className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <X size={13} /> Clear filters
          </button>
        )}
      </div>

      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-gray-500">
          Showing <span className="font-medium text-gray-700">{paginated.length}</span> of{' '}
          <span className="font-medium text-gray-700">{filtered.length}</span> companies
          {filtered.length !== pseCompanies.length && (
            <span className="text-gray-400"> (filtered from {pseCompanies.length})</span>
          )}
        </p>
        {totalPages > 1 && (
          <p className="text-sm text-gray-500">Page {page + 1} of {totalPages}</p>
        )}
      </div>


      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Company</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Sector</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Missions and Models</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">NASA Alumni</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {paginated.map(({ company, sector }, i) => {
              const eng = MOCK_ENGAGEMENT[company];
              const models = eng ? eng.models : (sectorModelMap[sector] || []);
              const statusMeta = eng ? STATUS_META[eng.status] : null;
              return (
                <tr key={`${company}-${i}`} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-800">{company}</td>
                  <td className="px-4 py-3"><SectorBadge sector={sector} /></td>
                  <td className="px-4 py-3">
                    {statusMeta ? (
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${statusMeta.color}`}>
                        {statusMeta.label}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-300">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {models.slice(0, 4).map(m => (
                        <ModelBadge key={m} name={m} color={modelColorMap[m]} />
                      ))}
                      {!eng && models.length > 0 && (
                        <span className="text-xs text-gray-300 italic self-center">sector-inferred</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {(() => {
                      const people = alumni[company] || [];
                      if (people.length === 0) return <span className="text-gray-300 text-xs">—</span>;
                      return (
                        <div className="flex flex-wrap gap-1">
                          {people.slice(0, 3).map((p, i) => (
                            <a
                              key={i}
                              href={p.linkedin}
                              target="_blank"
                              rel="noopener noreferrer"
                              title={`${p.name}: ${p.title}`}
                              className="flex items-center gap-0.5 text-xs text-violet-700 hover:text-violet-900 font-medium"
                            >
                              <User size={11} />
                              {p.name.split(' ').filter(Boolean).at(-1)}
                            </a>
                          ))}
                          {people.length > 3 && (
                            <span className="text-xs text-gray-400">+{people.length - 3}</span>
                          )}
                        </div>
                      );
                    })()}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <p className="text-center text-gray-400 py-12 text-sm">No companies match your filters</p>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 mt-4">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
          >
            ← Previous
          </button>
          <div className="flex gap-1">
            {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
              const p = totalPages <= 7 ? i : (page < 4 ? i : (page > totalPages - 4 ? totalPages - 7 + i : page - 3 + i));
              return (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`w-8 h-8 text-sm rounded-lg transition-colors ${
                    p === page ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {p + 1}
                </button>
              );
            })}
          </div>
          <button
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page === totalPages - 1}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
};

// ─── Models for Industry ──────────────────────────────────────────────────────

const ModelsForIndustry = ({ sectorCounts }) => {
  const modelSectorMap = useMemo(() => {
    const map = {};
    ALL_MODELS.forEach(m => { map[m.name] = []; });
    Object.entries(SECTOR_MAP).forEach(([sector, data]) => {
      data.models.forEach(({ name }) => {
        if (map[name]) map[name].push(sector);
      });
    });
    return map;
  }, []);

  const modelCompanyCount = useMemo(() => {
    const counts = {};
    ALL_MODELS.forEach(m => { counts[m.name] = 0; });
    Object.entries(SECTOR_MAP).forEach(([sector, data]) => {
      data.models.forEach(({ name }) => {
        counts[name] = (counts[name] || 0) + (sectorCounts[sector] || 0);
      });
    });
    return counts;
  }, [sectorCounts]);

  const ModelCard = ({ model }) => {
    const sectors = modelSectorMap[model.name] || [];
    const companyCount = modelCompanyCount[model.name] || 0;
    const displaySectors = sectors.slice(0, 4);
    const extra = sectors.length - displaySectors.length;

    return (
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-lg transition-shadow flex flex-col">
        <div className="h-1.5 flex-shrink-0" style={{ backgroundColor: model.color }} />
        <div className="p-5 flex flex-col flex-1">
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1 min-w-0 pr-2">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {model.type === 'mission' ? 'NASA Mission' : 'NASA Model'}
              </p>
              <h3 className="text-xl font-bold text-gray-900 mt-0.5">{model.name}</h3>
              <p className="text-xs text-gray-400 mt-0.5">{model.domain}</p>
            </div>
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: `${model.color}1a` }}
            >
              {model.type === 'mission'
                ? <Satellite size={18} style={{ color: model.color }} />
                : <FlaskConical size={18} style={{ color: model.color }} />
              }
            </div>
          </div>

          <p className="text-sm text-gray-700 leading-relaxed mb-4 flex-1">{model.industryPitch}</p>

          {/* Sector tags */}
          <div className="flex flex-wrap gap-1 mb-4">
            {displaySectors.map(sector => (
              <span key={sector} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full">
                {sector}
              </span>
            ))}
            {extra > 0 && (
              <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-400 rounded-full">
                +{extra} more
              </span>
            )}
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-gray-100">
            <p className="text-xs text-gray-500">
              <span className="font-semibold text-gray-700">{companyCount}</span> companies ·{' '}
              <span className="font-semibold text-gray-700">{sectors.length}</span> sectors
            </p>
            <div className="flex items-center gap-3">
              {model.website && (
                <a
                  href={model.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-gray-400 hover:text-indigo-600 flex items-center gap-0.5 transition-colors"
                >
                  <ExternalLink size={11} /> Site
                </a>
              )}
              <Link
                to={model.path}
                className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-0.5 transition-colors"
              >
                Dashboard <ChevronRight size={13} />
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const featuredMissions = ALL_MODELS.filter(m => m.type === 'mission' && ['GRACE', 'SWOT', 'TROPESS'].includes(m.name));
  const featuredModels = ALL_MODELS.filter(m => m.type === 'model' && ['ECCO', 'ISSM', 'CMS-Flux'].includes(m.name));

  return (
    <div className="space-y-10">
      <section>
        <div className="mb-5">
          <h2 className="text-xl font-bold text-gray-900">NASA Earth Missions</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            Satellite missions delivering global-scale Earth observations across hydrology, ocean, atmosphere, and cryosphere
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {featuredMissions.map(model => <ModelCard key={model.name} model={model} />)}
        </div>
      </section>

      <section>
        <div className="mb-5">
          <h2 className="text-xl font-bold text-gray-900">NASA's Earth Models</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            Physics-based Earth system models for ocean state estimation, ice sheet dynamics, and carbon flux quantification
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {featuredModels.map(model => <ModelCard key={model.name} model={model} />)}
        </div>
      </section>
    </div>
  );
};

// ─── News Feed ────────────────────────────────────────────────────────────────

const NewsSection = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cacheAge, setCacheAge] = useState(null);
  const [error, setError] = useState(null);
  const [modelFilter, setModelFilter] = useState('all');
  const [sectorFilter, setSectorFilter] = useState('all');
  const [companyFilter, setCompanyFilter] = useState('all');

  useEffect(() => {
    let cancelled = false;
    fetch(NEWS_JSON_URL)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(data => {
        if (cancelled) return;
        setArticles(data.articles || []);
        setCacheAge(data.fetchedAt || null);
        setLoading(false);
      })
      .catch(err => {
        if (!cancelled) { setError(err.message); setLoading(false); }
      });
    return () => { cancelled = true; };
  }, []);

  const allNewsModels = useMemo(() => {
    const s = new Set();
    articles.forEach(a => a.models.forEach(m => s.add(m)));
    return [...s].sort();
  }, [articles]);

  const allNewsSectors = useMemo(() => {
    const s = new Set();
    articles.forEach(a => a.sectors.forEach(sec => s.add(sec)));
    return [...s].sort();
  }, [articles]);

  const allNewsCompanies = useMemo(() => {
    const s = new Set();
    articles.forEach(a => {
      const haystack = a.title + ' ' + a.summary;
      COMPANY_PATTERNS.forEach(({ name, re }) => {
        if (re.test(haystack)) s.add(name);
      });
    });
    return [...s].sort();
  }, [articles]);

  const filtered = useMemo(() =>
    articles.filter(a => {
      const mMatch = modelFilter === 'all' || a.models.includes(modelFilter);
      const sMatch = sectorFilter === 'all' || a.sectors.includes(sectorFilter);
      const cMatch = companyFilter === 'all' || (() => {
        const { re } = COMPANY_PATTERNS.find(p => p.name === companyFilter) || {};
        return re ? re.test(a.title + ' ' + a.summary) : false;
      })();
      return mMatch && sMatch && cMatch;
    }),
    [articles, modelFilter, sectorFilter, companyFilter]
  );

  return (
    <div>
      {/* Header row */}
      <div className="flex items-center justify-between mb-5">
        <p className="text-xs text-gray-400">
          NASA · ScienceDaily · Eos/AGU · The Guardian · last 31 days · refreshed nightly at 2am PT
        </p>
        <div className="flex items-center gap-3">
          {!loading && cacheAge && (
            <span className="text-xs text-gray-400">
              Updated {new Date(cacheAge).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
          {!loading && <span className="text-xs text-gray-400">{articles.length} articles</span>}
        </div>
      </div>

      {/* Filters */}
      {!loading && articles.length > 0 && (
        <div className="flex flex-wrap gap-3 mb-6">
          <select
            value={modelFilter}
            onChange={e => setModelFilter(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 bg-white"
          >
            <option value="all">All Models & Missions</option>
            {allNewsModels.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
          <select
            value={sectorFilter}
            onChange={e => setSectorFilter(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 bg-white"
          >
            <option value="all">All Sectors</option>
            {allNewsSectors.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select
            value={companyFilter}
            onChange={e => setCompanyFilter(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-violet-200 bg-white"
          >
            <option value="all">All Companies</option>
            {allNewsCompanies.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          {(modelFilter !== 'all' || sectorFilter !== 'all' || companyFilter !== 'all') && (
            <button
              onClick={() => { setModelFilter('all'); setSectorFilter('all'); setCompanyFilter('all'); }}
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <X size={13} /> Clear
            </button>
          )}
        </div>
      )}

      {/* Loading skeleton (only when no cache) */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="border border-gray-100 rounded-xl p-5 animate-pulse">
              <div className="h-3 bg-gray-100 rounded w-1/3 mb-4" />
              <div className="h-4 bg-gray-100 rounded w-full mb-2" />
              <div className="h-4 bg-gray-100 rounded w-4/5 mb-4" />
              <div className="h-3 bg-gray-100 rounded w-2/3" />
            </div>
          ))}
        </div>
      )}

      {error && !articles.length && (
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <AlertCircle size={15} />
          Failed to load news: {error}
        </div>
      )}

      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filtered.map((article, i) => {
            const haystack = article.title + ' ' + article.summary;
            const mentionedCompanies = COMPANY_PATTERNS
              .filter(({ re }) => re.test(haystack))
              .map(({ name }) => name);
            return (
              <a
                key={i}
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="border border-gray-200 rounded-xl p-5 hover:shadow-md hover:border-blue-200 transition-all flex flex-col group"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="flex items-center gap-1.5 text-xs font-medium text-gray-500">
                    <Newspaper size={12} />
                    {article.section || article.source}
                  </span>
                  <span className="text-xs text-gray-400">{article.date}</span>
                </div>

                <h3 className="text-sm font-semibold text-gray-900 leading-snug mb-2 group-hover:text-blue-700 transition-colors">
                  {article.title}
                </h3>

                {article.summary ? (
                  <p
                    className="text-xs text-gray-500 leading-relaxed flex-1 mb-3 line-clamp-3"
                    dangerouslySetInnerHTML={{ __html: article.summary }}
                  />
                ) : (
                  <div className="flex-1" />
                )}

                {mentionedCompanies.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {mentionedCompanies.map(c => (
                      <span key={c} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-violet-50 text-violet-700 border border-violet-200">
                        <Building2 size={10} />
                        {c}
                      </span>
                    ))}
                  </div>
                )}

                <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                  <div className="flex flex-wrap gap-1">
                    {article.models.map(m => (
                      <span
                        key={m}
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium text-white"
                        style={{ backgroundColor: MODEL_COLORS[m] || '#6B7280' }}
                      >
                        {m}
                      </span>
                    ))}
                    {article.sectors.map(s => (
                      <span key={s} className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                        {s}
                      </span>
                    ))}
                    {article.models.length === 0 && article.sectors.length === 0 && (
                      <span className="text-xs text-gray-300 italic">general</span>
                    )}
                  </div>
                  <ExternalLink size={13} className="text-gray-300 group-hover:text-blue-400 transition-colors flex-shrink-0 ml-2" />
                </div>
              </a>
            );
          })}
        </div>
      )}

      {!loading && filtered.length === 0 && articles.length > 0 && (
        <div className="text-center text-gray-400 py-16 text-sm">No articles match your filters</div>
      )}
      {!loading && articles.length === 0 && !error && (
        <div className="text-center text-gray-400 py-16 text-sm">No articles returned. Try again later</div>
      )}
    </div>
  );
};

// ─── Main PSEPage ─────────────────────────────────────────────────────────────

const PSEPage = () => {
  const [activeTab, setActiveTab] = useState('models');
  const [alumni, setAlumni] = useState({});

  useEffect(() => {
    fetch(ALUMNI_JSON_URL)
      .then(r => r.json())
      .then(data => setAlumni(data.alumni || {}))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const prev = document.title;
    const favicon = document.querySelector('link[rel="icon"]');
    const prevHref = favicon?.href;
    document.title = 'PSE';
    if (favicon) favicon.href = `${process.env.PUBLIC_URL}/favicon-pse.svg`;
    return () => {
      document.title = prev;
      if (favicon && prevHref) favicon.href = prevHref;
    };
  }, []);

  const sectorCounts = useMemo(() => {
    const counts = {};
    pseCompanies.forEach(({ sector }) => {
      counts[sector] = (counts[sector] || 0) + 1;
    });
    return counts;
  }, []);

  const uniqueSectors = Object.keys(sectorCounts).length;

  return (
    <div className="bg-gray-100 min-h-screen">
      <PSENavBar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="max-w-7xl mx-auto px-4 py-6">
        <Hero companiesCount={pseCompanies.length} sectorsCount={uniqueSectors} />

        <div className="bg-white rounded-lg shadow-sm p-6">
          {activeTab === 'sectors' && <SectorExplorer sectorCounts={sectorCounts} alumni={alumni} />}
          {activeTab === 'companies' && <CompanyDirectory sectorCounts={sectorCounts} alumni={alumni} />}
          {activeTab === 'models' && <ModelsForIndustry sectorCounts={sectorCounts} />}
          {activeTab === 'news' && <NewsSection />}
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default PSEPage;
