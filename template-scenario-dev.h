/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2012 Federal University of Uberlândia
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 3 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, see <http://www.gnu.org/licenses/>.
 *
 * Author: Saulo da Mata <damata.saulo@gmail.com>
 *
 */

#include "../channel/LteChannel.h"
#include "../phy/enb-lte-phy.h"
#include "../phy/ue-lte-phy.h"
#include "../core/spectrum/bandwidth-manager.h"
#include "../networkTopology/Cell.h"
#include "../protocolStack/packet/packet-burst.h"
#include "../protocolStack/packet/Packet.h"
#include "../core/eventScheduler/simulator.h"
#include "../flows/application/InfiniteBuffer.h"
#include "../flows/application/VoIP.h"
#include "../flows/application/CBR.h"
#include "../flows/application/TraceBased.h"
#include "../device/IPClassifier/ClassifierParameters.h"
#include "../flows/QoS/QoSParameters.h"
#include "../flows/QoS/QoSForEXP.h"
#include "../flows/QoS/QoSForFLS.h"
#include "../flows/QoS/QoSForM_LWDF.h"
#include "../componentManagers/FrameManager.h"
#include "../utility/seed.h"
#include "../utility/RandomVariable.h"
#include "../phy/wideband-cqi-eesm-error-model.h"
#include "../phy/simple-error-model.h"
#include "../channel/propagation-model/macrocell-urban-area-channel-realization.h"
#include "../load-parameters.h"
#include <queue>
#include <fstream>
#include <stdlib.h>
#include <cstring>
#include <iostream>
#include <algorithm>

const char COMMENT_CHAR = '#';


static void TemplateScenario (int n_ue, string scheduler_type, int seed)
{

  fstream f_setup;
  map<string, string> par_map;

  double sim_time = 0.0;
  double sim_time_flow = 0.0;
  double dl_bw = 0.0;
  int n_cells = 0;
  int clusters = 0;
  double radius = 0.0;
  int n_voip = 0;
  int n_video = 0;
  int n_be = 0;
  int n_cbr = 0;
  string frame_struct;
  int user_speed = 0;
  double max_delay = 0.0;
  int video_bit_rate = 0;
  int cqi_reporting_interval = 0;
  bool handover;


  //Opening setup file
  f_setup.open("/home/saulo/dev/lte-sim-helper/setup-dev.cfg");
  if (f_setup.is_open())
    cout<<"Setup file successfully open!"<<endl;
  else
    {
      cout<<"Error: unable to open setup.cfg!!" << endl;
      exit(0);
    }

  //Getting parameters from setup file.
  char line [512];
  while (f_setup.getline (line, 512))
    {
      if ((line[0] != COMMENT_CHAR) && (line[0] != '\n') && (line[0] != '\0'))
          {
            string tmp = line;
            string::size_type i = tmp.find_first_of ("=");
            string key = tmp.substr (0, i);
            key.erase(remove(key.begin(), key.end(), ' '), key.end());
            string value = tmp.substr (i + 1, string::npos);
            value.erase(remove(value.begin(), value.end(), ' '), value.end());
            par_map.insert (pair<string, string>(key, value));
          }
    }

  sim_time = atof(par_map["SIM_TIME"].c_str());
  sim_time_flow = atof(par_map["SIM_TIME_FLOW"].c_str());
  dl_bw = atof(par_map["DL_BW"].c_str());
  n_cells = atoi(par_map["N_CELLS"].c_str());
  radius = atof(par_map["RADIUS"].c_str());
  clusters = atoi(par_map["CLUSTERS"].c_str());
  n_voip = atoi(par_map["N_VOIP"].c_str());
  n_video = atoi(par_map["N_VIDEO"].c_str());
  n_be = atoi(par_map["N_BE"].c_str());
  n_cbr = atoi(par_map["N_CBR"].c_str());
  frame_struct = par_map["FRAME_STRUCT"];
  user_speed = atoi(par_map["SPEED"].c_str());
  max_delay = atof(par_map["MAX_DELAY"].c_str());
  video_bit_rate = atoi(par_map["VIDEO_BIT_RATE"].c_str());
  cqi_reporting_interval = atoi(par_map["CQI_REP_INTERVAL"].c_str());

  if (not (par_map["HANDOVER"].compare("yes")))
    handover = 1;
  else
    handover = 0;

  // CREATE COMPONENT MANAGER
  Simulator *simulator = Simulator::Init();
  FrameManager *frameManager = FrameManager::Init();
  NetworkManager* networkManager = NetworkManager::Init();


  // CONFIGURE SEED
  if (seed >= 0)
    srand (seed);
  else
    srand (time(NULL));
  std::cout << "Simulation with SEED = " << seed << std::endl;


  // SET SCHEDULING ALLOCATION SCHEME
  ENodeB::DLSchedulerType dl_sched_type;
  if (not(scheduler_type.compare("PF")))
    {
      dl_sched_type = ENodeB::DLScheduler_TYPE_PROPORTIONAL_FAIR;
      cout << "Scheduler: " << scheduler_type << endl;
    }
  else if (not(scheduler_type.compare("MLWDF")))
    {
      dl_sched_type = ENodeB::DLScheduler_TYPE_MLWDF;
      cout << "Scheduler: " << scheduler_type << endl;
    }
  else if (not(scheduler_type.compare("EXP")))
    {
      dl_sched_type = ENodeB::DLScheduler_TYPE_EXP;
      cout << "Scheduler: " << scheduler_type << endl;
    }
  else if (not(scheduler_type.compare("FLS")))
    {
      dl_sched_type = ENodeB::DLScheduler_TYPE_FLS;
      cout << "Scheduler: " << scheduler_type << endl;
    }
  else if (not(scheduler_type.compare("EXP_RULE")))
    {
      dl_sched_type = ENodeB::DLScheduler_EXP_RULE;
      cout << "Scheduler: " << scheduler_type << endl;
    }
  else if (not(scheduler_type.compare("LOG_RULE")))
    {
      dl_sched_type = ENodeB::DLScheduler_LOG_RULE;
      cout << "Scheduler: " << scheduler_type << endl;
    }
  else if (not(scheduler_type.compare("MT")))
    {
      dl_sched_type = ENodeB::DLScheduler_TYPE_MAXIMUM_THROUGHPUT;
      cout << "Scheduler: " << scheduler_type << endl;
    }
  else
    {
      cout << "ERROR! Scheduler Type '" << scheduler_type << "' is not valid!" << endl;
      exit(0);
    }


  // SET FRAME STRUCTURE
  FrameManager::FrameStructure frame_structure;
  if (not(frame_struct.compare("FDD")))
    {
      frame_structure = FrameManager::FRAME_STRUCTURE_FDD;
      cout << "Frame Structure: " << frame_struct << endl;
    }
  else if (not(frame_struct.compare("TDD")))
    {
      frame_structure = FrameManager::FRAME_STRUCTURE_TDD;
      cout << "Frame Structure: " << frame_struct << endl;
    }
  else
    {
      cout<<"ERROR!! Frame structure '" << frame_struct << "' is not valid!" << endl;
      exit(0);
    }
  frameManager->SetFrameStructure(frame_structure);


  //SET Mobility Model
  Mobility::MobilityModel mobility_model;
  if (not(par_map["MOBILITY_MODEL"].compare("CONSTANT_POSITION")))
    mobility_model = Mobility::CONSTANT_POSITION;
  else if (not(par_map["MOBILITY_MODEL"].compare("RANDOM_DIRECTION")))
    mobility_model = Mobility::RANDOM_DIRECTION;
  else if (not(par_map["MOBILITY_MODEL"].compare("RANDOM_WALK")))
    mobility_model = Mobility::RANDOM_WALK;
  else if (not(par_map["MOBILITY_MODEL"].compare("RANDOM_WAYPOINT")))
    mobility_model = Mobility::RANDOM_WAYPOINT;
  else if (not(par_map["MOBILITY_MODEL"].compare("MANHATTAN")))
    mobility_model = Mobility::MANHATTAN;
  else
    {
      cout<<"ERROR!! Mobility Model '" << par_map["MOBILITY_MODEL"] << "' is not valid!" << endl;
      exit(0);
    }



    //create cells
    std::vector <Cell*> *cells = new std::vector <Cell*>;
    for (int i = 0; i < n_cells; i++)
          {
            CartesianCoordinates center =
                            GetCartesianCoordinatesForCell(i, radius * 1000.);

            Cell *c = new Cell (i, radius, 0.035, center.GetCoordinateX (), center.GetCoordinateY ());
            cells->push_back (c);
            networkManager->GetCellContainer ()->push_back (c);

            std::cout << "Created Cell, id " << c->GetIdCell ()
                            <<", position: " << c->GetCellCenterPosition ()->GetCoordinateX ()
                            << " " << c->GetCellCenterPosition ()->GetCoordinateY () << std::endl;
          }
    std::vector <BandwidthManager*> spectrums = RunFrequencyReuseTechniques (n_cells, clusters, dl_bw);

    //Create a set of a couple of channels
    std::vector <LteChannel*> *dlChannels = new std::vector <LteChannel*>;
    std::vector <LteChannel*> *ulChannels = new std::vector <LteChannel*>;
    for (int i= 0; i < n_cells; i++)
      {
        LteChannel *dlCh = new LteChannel ();
        dlCh->SetChannelId (i);
        dlChannels->push_back (dlCh);

        LteChannel *ulCh = new LteChannel ();
        ulCh->SetChannelId (i);
        ulChannels->push_back (ulCh);
      }

    //create eNBs
    std::vector <ENodeB*> *eNBs = new std::vector <ENodeB*>;
    for (int i = 0; i < n_cells; i++)
          {
            ENodeB* enb = new ENodeB (i, cells->at (i));
            enb->GetPhy ()->SetDlChannel (dlChannels->at (i));
            enb->GetPhy ()->SetUlChannel (ulChannels->at (i));

            enb->SetDLScheduler (dl_sched_type);

            enb->GetPhy ()->SetBandwidthManager (spectrums.at (i));

            std::cout << "Created enb, id " << enb->GetIDNetworkNode()
                            << ", cell id " << enb->GetCell ()->GetIdCell ()
                            <<", position: " << enb->GetMobilityModel ()->GetAbsolutePosition ()->GetCoordinateX ()
                            << " " << enb->GetMobilityModel ()->GetAbsolutePosition ()->GetCoordinateY ()
                            << ", channels id " << enb->GetPhy ()->GetDlChannel ()->GetChannelId ()
                            << enb->GetPhy ()->GetUlChannel ()->GetChannelId ()  << std::endl;

            spectrums.at (i)->Print ();


            ulChannels->at (i)->AddDevice((NetworkNode*) enb);


            networkManager->GetENodeBContainer ()->push_back (enb);
            eNBs->push_back (enb);
          }

  //Define Application Container
  int cell_app = 1;
  VoIP VoIPApplication[n_voip*cell_app*n_ue];
  TraceBased VideoApplication[n_video*cell_app*n_ue];
  InfiniteBuffer BEApplication[n_be*cell_app*n_ue];
  CBR CBRApplication[n_cbr*cell_app*n_ue];

  int voipApplication = 0;
  int videoApplication = 0;
  int cbrApplication = 0;
  int beApplication = 0;
  int destinationPort = 101;
  int applicationID = 0;


  //Create GW
  Gateway *gw = new Gateway ();
  networkManager->GetGatewayContainer ()->push_back (gw);

  int maxXY = radius * 1000;
  //Create UEs
  int idUE = n_cells;
  for (int i = 0; i < n_ue; i++)
        {
          //ue's random position
	  double posX = GetRandomVariable (maxXY); // (double) (rand() %maxXY);
	  double posY = GetRandomVariable (maxXY); // (double) (rand() %maxXY);
	  double speedDirection = GetRandomVariable (360.) * ((2.*3.14)/360.);


	  UserEquipment* ue = new UserEquipment (idUE,
		                                 posX, posY, user_speed, speedDirection,
						 cells->at (0),
						 eNBs->at (0),
		                                 handover, //handover false!
		                                 mobility_model);

	  std::cout << "Created UE - id " << idUE << " position " << posX << " " << posY << " direction " << speedDirection << std::endl;

	  ue->GetMobilityModel()->GetAbsolutePosition()->Print();
	  ue->GetPhy ()->SetDlChannel (eNBs->at (0)->GetPhy ()->GetDlChannel ());
	  ue->GetPhy ()->SetUlChannel (eNBs->at (0)->GetPhy ()->GetUlChannel ());
        
          if ((not(par_map["CQI_METHOD"].compare("FULL_BANDWIDTH"))) and (not(par_map["CQI_REP_MODE"].compare("PERIODIC"))))
            {
              FullbandCqiManager *cqiManager = new FullbandCqiManager ();
              cqiManager->SetCqiReportingMode (CqiManager::PERIODIC);
              cqiManager->SetReportingInterval (cqi_reporting_interval);
              cqiManager->SetDevice (ue);
              ue->SetCqiManager (cqiManager);
            }
          else if ((not(par_map["CQI_METHOD"].compare("FULL_BANDWIDTH"))) and (not(par_map["CQI_REP_MODE"].compare("APERIODIC"))))
            {
              FullbandCqiManager *cqiManager = new FullbandCqiManager ();
              cqiManager->SetCqiReportingMode (CqiManager::APERIODIC);
              cqiManager->SetReportingInterval (cqi_reporting_interval);
              cqiManager->SetDevice (ue);
              ue->SetCqiManager (cqiManager);
            }
          else
            {
              cout<<"ERROR!! CQI Method '" << par_map["CQI_METHOD"] << "' or CQI Reporting Mode '"
                  << par_map["CQI_REP_MODE"] << "' is not valid!" << endl;
              exit(0);
            }



          WidebandCqiEesmErrorModel *errorModel = new WidebandCqiEesmErrorModel ();
          ue->GetPhy ()->SetErrorModel (errorModel);

	  networkManager->GetUserEquipmentContainer ()->push_back (ue);

	  // register ue to the enb
	  eNBs->at (0)->RegisterUserEquipment (ue);

	  // define the channel realization
	  if(not(par_map["PROP_MODEL"].compare("MACRO_CELL_URBAN_MODEL")))
	    {
	      MacroCellUrbanAreaChannelRealization* c = new MacroCellUrbanAreaChannelRealization (eNBs->at (0), ue);
              c->SetChannelType (ChannelRealization::CHANNEL_TYPE_PED_A);
              eNBs->at (0)->GetPhy ()->GetDlChannel ()->GetPropagationLossModel ()->AddChannelRealization (c);
	    }
          else
            {
              cout<<"ERROR!! Propagation model '" << par_map["PROP_MODEL"] << "' is not valid!" << endl;
              exit(0);
            }


	  // CREATE DOWNLINK APPLICATION FOR THIS UE
	  double start_time = 0.1 + GetRandomVariable (5.);
	  double duration_time = start_time + sim_time_flow;

	  // *** voip application
	  for (int j = 0; j < n_voip; j++)
		{
		  // create application
		  VoIPApplication[voipApplication].SetSource (gw);
		  VoIPApplication[voipApplication].SetDestination (ue);
		  VoIPApplication[voipApplication].SetApplicationID (applicationID);
		  VoIPApplication[voipApplication].SetStartTime(start_time);
		  VoIPApplication[voipApplication].SetStopTime(duration_time);

		  // create qos parameters
		  if (dl_sched_type == ENodeB::DLScheduler_TYPE_FLS)
			{
			  QoSForFLS *qos = new QoSForFLS ();
			  qos->SetMaxDelay (max_delay);
			  if (max_delay == 0.1)
				{
				  std::cout << "Target Delay = 0.1 s, M = 9" << std::endl;
				  qos->SetNbOfCoefficients (9);
				}
			  else if (max_delay == 0.08)
				{
				  std::cout << "Target Delay = 0.08 s, M = 7" << std::endl;
				  qos->SetNbOfCoefficients (7);
				}
			  else if (max_delay == 0.06)
				{
				  std::cout << "Target Delay = 0.06 s, M = 5" << std::endl;
				  qos->SetNbOfCoefficients (5);
				}
			  else if (max_delay == 0.04)
				{
				  std::cout << "Target Delay = 0.04 s, M = 3" << std::endl;
				  qos->SetNbOfCoefficients (3);
				}
			  else
				{
				  std::cout << "ERROR: target delay is not available"<< std::endl;
				  return;
				}

			  VoIPApplication[voipApplication].SetQoSParameters (qos);
			}
		  else if (dl_sched_type == ENodeB::DLScheduler_TYPE_EXP)
			{
			  QoSForEXP *qos = new QoSForEXP ();
			  qos->SetMaxDelay (max_delay);
			  VoIPApplication[voipApplication].SetQoSParameters (qos);
			}
		  else if (dl_sched_type == ENodeB::DLScheduler_TYPE_MLWDF)
			{
			  QoSForM_LWDF *qos = new QoSForM_LWDF ();
			  qos->SetMaxDelay (max_delay);
			  VoIPApplication[voipApplication].SetQoSParameters (qos);
			}
		  else
			{
			  QoSParameters *qos = new QoSParameters ();
			  qos->SetMaxDelay (max_delay);
			  VoIPApplication[voipApplication].SetQoSParameters (qos);
			}


		  //create classifier parameters
		  ClassifierParameters *cp = new ClassifierParameters (gw->GetIDNetworkNode(),
        						                ue->GetIDNetworkNode(),
							                0, //source port
								        destinationPort,
						                        TransportProtocol::TRANSPORT_PROTOCOL_TYPE_UDP);
		  VoIPApplication[voipApplication].SetClassifierParameters (cp);

		  std::cout << "CREATED VOIP APPLICATION, ID " << applicationID << std::endl;

		  //update counter
		  destinationPort++;
		  applicationID++;
		  voipApplication++;
		}


	  // *** video application
	  for (int j = 0; j < n_video; j++)
		{
		  // create application
		  VideoApplication[videoApplication].SetSource (gw);
		  VideoApplication[videoApplication].SetDestination (ue);
		  VideoApplication[videoApplication].SetApplicationID (applicationID);
		  VideoApplication[videoApplication].SetStartTime(start_time);
		  VideoApplication[videoApplication].SetStopTime(duration_time);

		  string video_trace ("foreman_H264_");
		  //string video_trace ("highway_H264_");
		  //string video_trace ("mobile_H264_");

		  switch (video_bit_rate)
			  {
				case 128:
				  {
				    string _file (path + "src/flows/application/Trace/" + video_trace + "128k.dat");
				    VideoApplication[videoApplication].SetTraceFile(_file);
				    std::cout << "		selected video @ 128k " << _file << std::endl;
				    break;
				  }
				case 242:
				  {
				        string _file (path + "src/flows/application/Trace/" + video_trace + "242k.dat");
				    VideoApplication[videoApplication].SetTraceFile(_file);
				    std::cout << "		selected video @ 242k"<< std::endl;
				    break;
				  }
				case 440:
				  {
				    string _file (path + "src/flows/application/Trace/" + video_trace + "440k.dat");
 			        VideoApplication[videoApplication].SetTraceFile(_file);
				    std::cout << "		selected video @ 440k"<< std::endl;
				    break;
				  }
				default:
				  {
				    string _file (path + "src/flows/application/Trace/" + video_trace + "128k.dat");
				    VideoApplication[videoApplication].SetTraceFile(_file);
				    std::cout << "		selected video @ 128k as default"<< std::endl;
				    break;
				  }
			  }

		  // create qos parameters
		  if (dl_sched_type == ENodeB::DLScheduler_TYPE_FLS)
			{
			  QoSForFLS *qos = new QoSForFLS ();
			  qos->SetMaxDelay (max_delay);
			  if (max_delay == 0.1)
				{
				  std::cout << "Target Delay = 0.1 s, M = 9" << std::endl;
				  qos->SetNbOfCoefficients (9);
				}
			  else if (max_delay == 0.08)
				{
				  std::cout << "Target Delay = 0.08 s, M = 7" << std::endl;
				  qos->SetNbOfCoefficients (7);
				}
			  else if (max_delay == 0.06)
				{
				  std::cout << "Target Delay = 0.06 s, M = 5" << std::endl;
				  qos->SetNbOfCoefficients (5);
				}
			  else if (max_delay == 0.04)
				{
				  std::cout << "Target Delay = 0.04 s, M = 3" << std::endl;
				  qos->SetNbOfCoefficients (3);
				}
			  else
				{
				  std::cout << "ERROR: target delay is not available"<< std::endl;
				  return;
				}
			  VideoApplication[videoApplication].SetQoSParameters (qos);
			}
		  else if (dl_sched_type == ENodeB::DLScheduler_TYPE_EXP)
			{
			  QoSForEXP *qos = new QoSForEXP ();
			  qos->SetMaxDelay (max_delay);
			  VideoApplication[videoApplication].SetQoSParameters (qos);
			}
		  else if (dl_sched_type == ENodeB::DLScheduler_TYPE_MLWDF)
			{
			  QoSForM_LWDF *qos = new QoSForM_LWDF ();
			  qos->SetMaxDelay (max_delay);
			  VideoApplication[videoApplication].SetQoSParameters (qos);
			}
		  else
			{
			  QoSParameters *qos = new QoSParameters ();
			  qos->SetMaxDelay (max_delay);
			  VideoApplication[videoApplication].SetQoSParameters (qos);
			}


		  //create classifier parameters
		  ClassifierParameters *cp = new ClassifierParameters (gw->GetIDNetworkNode(),
						                        ue->GetIDNetworkNode(),
						                        0,
						                        destinationPort,
						                        TransportProtocol::TRANSPORT_PROTOCOL_TYPE_UDP);
		  VideoApplication[videoApplication].SetClassifierParameters (cp);

		  std::cout << "CREATED VIDEO APPLICATION, ID " << applicationID << std::endl;

		  //update counter
		  destinationPort++;
		  applicationID++;
		  videoApplication++;
		}

	  // *** be application
	  for (int j = 0; j < n_be; j++)
		{
		  // create application
		  BEApplication[beApplication].SetSource (gw);
		  BEApplication[beApplication].SetDestination (ue);
		  BEApplication[beApplication].SetApplicationID (applicationID);
		  BEApplication[beApplication].SetStartTime(start_time);
		  BEApplication[beApplication].SetStopTime(duration_time);


		  // create qos parameters
		  QoSParameters *qosParameters = new QoSParameters ();
		  BEApplication[beApplication].SetQoSParameters (qosParameters);


		  //create classifier parameters
		  ClassifierParameters *cp = new ClassifierParameters (gw->GetIDNetworkNode(),
						                        ue->GetIDNetworkNode(),
						                        0,
						                        destinationPort,
					                                TransportProtocol::TRANSPORT_PROTOCOL_TYPE_UDP);
		  BEApplication[beApplication].SetClassifierParameters (cp);

		  std::cout << "CREATED BE APPLICATION, ID " << applicationID << std::endl;

		  //update counter
		  destinationPort++;
		  applicationID++;
		  beApplication++;
		}

	  // *** cbr application
	  for (int j = 0; j < n_cbr; j++)
		{
		  // create application
		  CBRApplication[cbrApplication].SetSource (gw);
		  CBRApplication[cbrApplication].SetDestination (ue);
		  CBRApplication[cbrApplication].SetApplicationID (applicationID);
		  CBRApplication[cbrApplication].SetStartTime(start_time);
		  CBRApplication[cbrApplication].SetStopTime(duration_time);
		  CBRApplication[cbrApplication].SetInterval (0.04);
		  CBRApplication[cbrApplication].SetSize (5);

		  // create qos parameters
		  QoSParameters *qosParameters = new QoSParameters ();
		  qosParameters->SetMaxDelay (max_delay);

		  CBRApplication[cbrApplication].SetQoSParameters (qosParameters);


		  //create classifier parameters
		  ClassifierParameters *cp = new ClassifierParameters (gw->GetIDNetworkNode(),
					                                ue->GetIDNetworkNode(),
							                0,
							                destinationPort,
							                TransportProtocol::TRANSPORT_PROTOCOL_TYPE_UDP);
		  CBRApplication[cbrApplication].SetClassifierParameters (cp);

		  std::cout << "CREATED CBR APPLICATION, ID " << applicationID << std::endl;

		  //update counter
		  destinationPort++;
		  applicationID++;
		  cbrApplication++;
		}

	  idUE++;

	}



  simulator->SetStop(sim_time);
  //simulator->Schedule(duration-10, &Simulator::PrintMemoryUsage, simulator);
  simulator->Run ();



  //Delete created objects
  cells->clear ();
  delete cells;
  eNBs->clear ();
  delete eNBs;
  delete frameManager;
  //delete networkManager;
  delete simulator;

}
